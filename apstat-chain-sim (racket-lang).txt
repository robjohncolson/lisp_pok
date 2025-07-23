#lang racket
(require json plot racket/gui/base)

;; Data Types (schemas)
(struct payload (answer hash) #:transparent)
(struct transaction (id timestamp owner-pubkey question-id type payload) #:transparent)
(struct block (hash txns) #:transparent)
(struct question (id prompt qtype) #:transparent)
(define *app-db* (make-hash)) ; Central state (mutable hash for REPL)

;; Helpers for serialization
(define (payload->hash p)
  (hash 'answer (payload-answer p) 'hash (payload-hash p)))

(define (transaction->hash txn)
  (hash 'id (transaction-id txn)
        'timestamp (transaction-timestamp txn)
        'owner-pubkey (transaction-owner-pubkey txn)
        'question-id (transaction-question-id txn)
        'type (transaction-type txn)
        'payload (payload->hash (transaction-payload txn))))

(define (block->hash b)
  (hash 'hash (block-hash b) 'txns (map transaction->hash (block-txns b))))

;; Pure Functions
(define (create-txn qid pubkey ans t type)
  (let ([hash (number->string (equal-hash-code ans))])
    (transaction (format "~a-~a" t type) t pubkey qid type (payload ans hash))))

(define (valid-txn? txn)
  (and (not (string=? (transaction-owner-pubkey txn) ""))
       (not (string=? (transaction-question-id txn) ""))
       (not (string=? (payload-hash (transaction-payload txn)) ""))
       (> (transaction-timestamp txn) 0)
       (member (transaction-type txn) '("completion" "attestation"))))

(define (add-tx-to-mempool txn)
  (hash-update! *app-db* 'mempool (lambda (mp) (cons txn (or mp '()))) '()))

(define (find-question-by-id q-id)
  (findf (lambda (q) (string=? (question-id q) q-id)) (hash-ref *app-db* 'curriculum '())))

(define (group-attestations attns)
  (let ([dist (make-hash)])
    (for-each (lambda (txn) 
                (when (string=? (transaction-type txn) "attestation")
                  (hash-update! dist (payload-hash (transaction-payload txn)) add1 0))) attns)
    dist))

(define (calculate-convergence qid)
  (let* ([all-txns (append (hash-ref *app-db* 'mempool '()) 
                           (apply append (map block-txns (hash-ref *app-db* 'chain '()))))]
         [attns (filter (lambda (txn) (and (string=? (transaction-question-id txn) qid)
                                           (string=? (transaction-type txn) "attestation"))) all-txns)]
         [dist (group-attestations attns)]
         [total (apply + (hash-values dist))]
         [max-count (if (zero? (hash-count dist)) 0 (apply max (hash-values dist)))])
    (if (zero? total) 0.0 (exact->inexact (/ max-count total)))))

(define (calculate-frq-convergence qid)
  (let* ([all-txns (append (hash-ref *app-db* 'mempool '()) 
                           (apply append (map block-txns (hash-ref *app-db* 'chain '()))))]
         [attns (filter (lambda (txn) (and (string=? (transaction-question-id txn) qid)
                                           (string=? (transaction-type txn) "attestation"))) all-txns)]
         [scores (map (lambda (txn) (string->number (payload-answer (transaction-payload txn)))) attns)]
         [scores (filter number? scores)]
         [avg (if (null? scores) 0.0 (/ (apply + scores) (length scores)))]
         [variance (if (null? scores) 0.0 (/ (apply + (map (lambda (s) (expt (- s avg) 2)) scores)) (length scores)))]
         [sd (sqrt variance)])
    (printf "FRQ Stats - Avg: ~a, SD: ~a~%" avg sd)
    (if (zero? sd) 1.0 (exact->inexact (- 1.0 (/ sd 5.0))))))

(define (visualize-convergence qid)
  (let ([q (find-question-by-id qid)])
    (if (not q)
        (printf "Question ~a not found in curriculum.~%" qid)
        (let* ([all-txns (append (hash-ref *app-db* 'mempool '()) 
                                 (apply append (map block-txns (hash-ref *app-db* 'chain '()))))]
               [attns (filter (lambda (txn) (and (string=? (transaction-question-id txn) qid)
                                                 (string=? (transaction-type txn) "attestation"))) all-txns)]
               [data (if (string=? (question-qtype q) "frq")
                         (let ([scores (map (lambda (txn) (string->number (payload-answer (transaction-payload txn)))) attns)]
                               [dist (make-hash)])
                           (for-each (lambda (s) (when (number? s) (hash-update! dist s add1 0))) scores)
                           (map (lambda (k) (vector k (hash-ref dist k 0))) (hash-keys dist)))
                         (let ([dist (group-attestations attns)])
                           (map (lambda (k) (vector k (hash-ref dist k 0))) (hash-keys dist))))])
          (if (null? data)
              (printf "No attestations to visualize for ~a.~%" qid)
              (plot (discrete-histogram data)
                    #:title (format "~a Distribution" (if (string=? (question-qtype q) "frq") "FRQ Scores" "MCQ Attestations"))
                    #:x-label (if (string=? (question-qtype q) "frq") "Score" "Answer Hash")
                    #:y-label "Count"))))))

(define (propose-block)
  (let* ([mempool (hash-ref *app-db* 'mempool '())]
         [valid-txns (filter (lambda (txn)
                               (let* ([qid (transaction-question-id txn)]
                                      [conv (if (string=? (question-qtype (find-question-by-id qid)) "frq")
                                                (calculate-frq-convergence qid)
                                                (calculate-convergence qid))])
                                 (>= conv 0.8))) mempool)]
         [block-hash (format "~a-block" (length (hash-ref *app-db* 'chain '())))]
         [new-block (block block-hash valid-txns)])
    (when (not (null? valid-txns))
      (hash-update! *app-db* 'chain (lambda (ch) (cons new-block (or ch '()))) '())
      (hash-set! *app-db* 'mempool (remove* valid-txns mempool)))
    (printf "Block proposed: ~a~%" new-block)))

;; QR Sync (ADR-032)
(define (generate-qr-delta)
  (let ([state (hash-copy *app-db*)])
    (hash-remove! state 'curriculum)
    (let* ([serialized-chain (map block->hash (hash-ref state 'chain '()))]
           [serialized-mempool (map transaction->hash (hash-ref state 'mempool '()))]
           [str-state (hash 'chain serialized-chain 'mempool serialized-mempool)])
      (jsexpr->string str-state))))

(define (scan-qr qr-str)
  (let ([delta (string->jsexpr qr-str)])
    (hash-set! *app-db* 'mempool (map (lambda (t) (create-txn (hash-ref t 'question-id)
                                                              (hash-ref t 'owner-pubkey)
                                                              (hash-ref (hash-ref t 'payload) 'answer)
                                                              (hash-ref t 'timestamp)
                                                              (hash-ref t 'type))) (hash-ref delta 'mempool '())))
    (hash-set! *app-db* 'chain (map (lambda (b) (block (hash-ref b 'hash)
                                                       (map (lambda (t) (create-txn (hash-ref t 'question-id)
                                                                                   (hash-ref t 'owner-pubkey)
                                                                                   (hash-ref (hash-ref t 'payload) 'answer)
                                                                                   (hash-ref t 'timestamp)
                                                                                   (hash-ref t 'type))) (hash-ref b 'txns))))
                                    (hash-ref delta 'chain '())))
    (printf "QR scanned and merged.~%")))

;; Effectful Orchestration
(define (generate-new-identity)
  (format "pubkey-~a" (gensym)))

(define (init)
  (hash-set! *app-db* 'identity (generate-new-identity))
  (hash-set! *app-db* 'curriculum
             (list (question "U1-L2-Q01" "Categorical variable?" "mcq")
                   (question "U1-L10-Q04" "Explain normal distribution" "frq")))
  (hash-set! *app-db* 'mempool '())
  (hash-set! *app-db* 'chain '())
  (printf "Initialized with ~a questions.~%" (length (hash-ref *app-db* 'curriculum))))

(define (submit-answer qid ans #:type [type "completion"])
  (let ([pubkey (hash-ref *app-db* 'identity)]
        [t (current-inexact-milliseconds)])
    (let ([txn (create-txn qid pubkey ans t type)])
      (if (valid-txn? txn)
          (begin
            (add-tx-to-mempool txn)
            (printf "Txn added to mempool: ~a~%" txn))
          (printf "Invalid txn~%")))))

;; REPL Entry
(define (main)
  (init)
  (submit-answer "U1-L2-Q01" "B" #:type "attestation")
  (submit-answer "U1-L2-Q01" "B" #:type "attestation")
  (submit-answer "U1-L2-Q01" "B" #:type "attestation")
  (printf "MCQ Convergence: ~a~%" (calculate-convergence "U1-L2-Q01"))
  (propose-block)
  (printf "Chain: ~a~%" (hash-ref *app-db* 'chain))
  (submit-answer "U1-L10-Q04" "Response text" #:type "completion")
  (submit-answer "U1-L10-Q04" "4" #:type "attestation")
  (submit-answer "U1-L10-Q04" "5" #:type "attestation")
  (printf "FRQ Convergence: ~a~%" (calculate-frq-convergence "U1-L10-Q04"))
)

;; Enhanced GUI
(define frame (new frame% [label "APStat Chain Dashboard"] [width 600] [height 400]))

(define (update-display)
  (send msg set-label (format "Mempool: ~a txns\nChain: ~a blocks\nMCQ Conv: ~a\nFRQ Conv: ~a"
                              (length (hash-ref *app-db* 'mempool '()))
                              (length (hash-ref *app-db* 'chain '()))
                              (calculate-convergence "U1-L2-Q01")
                              (calculate-frq-convergence "U1-L10-Q04"))))

(define msg (new message% [parent frame] [label "Initialized"] [auto-resize #t]))

(define panel (new panel% [parent frame]))

(new button% [parent panel] [label "Submit MCQ (B)"] 
     [callback (lambda (b e) (submit-answer "U1-L2-Q01" "B" #:type "attestation") (update-display))])

(new button% [parent panel] [label "Submit FRQ (4)"] 
     [callback (lambda (b e) (submit-answer "U1-L10-Q04" "4" #:type "attestation") (update-display))])

(new button% [parent panel] [label "Propose Block"] 
     [callback (lambda (b e) (propose-block) (update-display))])

(new button% [parent panel] [label "Visualize MCQ"] 
     [callback (lambda (b e) (visualize-convergence "U1-L2-Q01"))])

(new button% [parent panel] [label "Visualize FRQ"] 
     [callback (lambda (b e) (visualize-convergence "U1-L10-Q04"))])

(new button% [parent panel] [label "Generate QR"] 
     [callback (lambda (b e) (printf "QR Delta: ~a~%" (generate-qr-delta)))])

(new text-field% [parent panel] [label "Scan QR:"] 
     [init-value ""] [stretchable-width #t]
     [callback (lambda (tf e) (if (eq? (send e get-event-type) 'text-field-enter)
                                  (begin (scan-qr (send tf get-value)) (update-display))
                                  (void)))])

(send frame show #t)

;; Step 1: Node Structure and Classroom Setup
(struct node (pubkey archetype mempool chain progress) #:transparent #:mutable) ; progress: current question index

;; Archetypes (accuracy profiles)
(define archetypes
  '((aces . 0.95) ; 95% correct MCQ, low FRQ SD
    (diligent . 0.8) ; 80% correct
    (strugglers . 0.6) ; 60% correct
    (guessers . 0.3))) ; 30% correct

;; Global Params (tunable)
(define total-nodes 40)
(define class-size 20)
(define accuracy-var 0.1) ; Variance around archetype accuracy
(define progress-lag-prob 0.1) ; 10% ahead/behind
(define sync-failure-prob 0.1) ; 10% sync fail
(define pairing-topology 'mixed) ; 'mixed (cross-class) or 'clique (within-class)
(define sim-days 180) ; Full year
(define meetings-per-week 4) ; 144 meetings
(define questions-per-day 5) ; ~4.5 avg for 817 questions
(define quorum-min-attest 3) ; Hybrid quorum
(define quorum-conv-thresh 0.8)

;; Load Curriculum
(define (load-curriculum)
  (with-input-from-file "curriculum.json"
    (lambda () (map (lambda (q) (question (hash-ref q 'id) (hash-ref q 'prompt) (hash-ref q 'qtype "mcq")))
                    (read-json)))))

(define curriculum (load-curriculum)) ; 817 questions

;; Create Node
(define (create-node id archetype)
  (node (format "pubkey-class~a-~a" (if (< id class-size) "A" "B") id)
        archetype
        '() ; mempool
        '() ; chain
        0)) ; progress

;; Setup Classrooms
(define (setup-classrooms)
  (let* ([arch-counts (hash 'aces 4 'diligent 24 'strugglers 8 'guessers 4)]
         [arch-list (append (make-list 4 'aces) (make-list 24 'diligent) (make-list 8 'strugglers) (make-list 4 'guessers))]
         [shuffled-arch (shuffle arch-list)])
    (define class-a (for/list ([i (in-range class-size)]) (create-node i (list-ref shuffled-arch i))))
    (define class-b (for/list ([i (in-range class-size)]) (create-node (+ i class-size) (list-ref shuffled-arch (+ i class-size)))))
    (hash-set! *app-db* 'class-a class-a)
    (hash-set! *app-db* 'class-b class-b)
    (printf "Setup: Class A ~a nodes, Class B ~a nodes.~%" class-size class-size)))

;; Inspect Node (REPL helper)
(define (inspect-node node)
  (printf "Node ~a (~a): Progress ~a/~a, Mempool ~a, Chain ~a~%" (node-pubkey node) (node-archetype node) (node-progress node) (length curriculum) (length (node-mempool node)) (length (node-chain node))))

;; Test in REPL
(setup-classrooms)
(inspect-node (car (hash-ref *app-db* 'class-a))) ; Sample node
(length curriculum) ; 817

;; Step 2: Daily Cycle & Txn Generation
(require math/statistics) ; For normal distribution

;; Helpers
(define (random-choice choices)
  (let ([keys (map (lambda (c) (hash-ref c 'key)) choices)])
    (list-ref keys (random (length keys)))))

(define (normal-random mean sd min-val max-val)
  (let ([sample (sample-normal 1 #:mean mean #:sd sd)])
    (max min-val (min max-val (round (car sample)))))) ; Clamp to [min-val, max-val]

(define (get-lesson-questions day)
  (let ([start (* day questions-per-day)]
        [end (min (+ start questions-per-day) (length curriculum))])
    (sublist curriculum start end)))

(define (generate-answer q archetype)
  (let ([accuracy (cdr (assoc archetype archetypes))])
    (if (string=? (question-qtype q) "mcq")
        (let ([choices (hash-ref q 'choices '())]
              [answerKey (hash-ref q 'answerKey #f)])
          (if (and answerKey (< (random) accuracy))
              answerKey
              (random-choice choices)))
        (let ([true-score 4.0] ; Latent true from rubric
              [sd (case archetype
                    [(aces) 0.5]
                    [(diligent) 0.8]
                    [(strugglers) 1.2]
                    [else #f])]) ; Guessers uniform
          (if sd
              (number->string (normal-random true-score sd 1 5))
              (number->string (add1 (random 5))))))) ; Uniform 1-5

(define (generate-completion-txn node q)
  (let ([ans (if (string=? (question-qtype q) "mcq")
                 (generate-answer q (node-archetype node))
                 (format "FRQ Response for ~a by ~a" (question-id q) (node-pubkey node)))]
        [t (current-inexact-milliseconds)])
    (create-txn (question-id q) (node-pubkey node) ans t "completion")))

(define (sublist lst start end)
  (take (drop lst start) (- end start)))

(define (average lst)
  (/ (apply + lst) (length lst)))

(define (inspect-node-txns node)
  (printf "Node ~a (~a) txns: ~a~%"
          (node-pubkey node)
          (node-archetype node)
          (map (lambda (t) (list (transaction-question-id t) (transaction-type t) (payload-answer (transaction-payload t))))
               (node-mempool node))))

;; Daily Cycle
(define (run-day day)
  (let ([all-nodes (append (hash-ref *app-db* 'class-a) (hash-ref *app-db* 'class-b))])
    (for-each
     (lambda (node)
       (let ([lag (if (< (random) progress-lag-prob)
                      (if (< (random) 0.5) questions-per-day (- questions-per-day))
                      0)]) ; ±5 questions
         (set-node-progress! node (max 0 (+ (node-progress node) lag questions-per-day)))
         (let ([questions (get-lesson-questions day)])
           (for-each
            (lambda (q)
              (set-node-mempool! node (cons (generate-completion-txn node q) (node-mempool node))))
            questions))))
     all-nodes)
    (printf "Day ~a complete. Avg progress: ~a questions.~%" day (average (map node-progress all-nodes)))))

;; Test in REPL
(setup-classrooms)
(run-day 1)
(inspect-node-txns (car (hash-ref *app-db* 'class-a)))


;; Step 3: Meeting Cycle & Sync/Attest
;; Helpers
(define (merkle-hash chain)
  (number->string (equal-hash-code (map (lambda (b) (block-hash b)) chain)))) ; Simple hash-of-hashes

(define (sync-delta node partner)
  (let ([delta (generate-qr-delta partner)]
        [my-merkle (merkle-hash (node-chain node))]
        [partner-merkle (merkle-hash (node-chain partner))])
    (if (string=? my-merkle partner-merkle)
        node
        (if (> (length (node-chain partner)) (length (node-chain node))
            (begin (set-node-chain! node (node-chain partner))
                   (for-each (lambda (txn) (set-node-mempool! node (cons txn (node-mempool node)))) (node-mempool partner))
                   node)
            node)))) ; Discard shorter, adopt longer, process mempool

(define (attest-partner node partner)
  (let ([pending (filter (lambda (txn) (string=? (transaction-type txn) "completion")) (node-mempool partner))]
        [num-attest (add1 (random 3))]) ; Uniform 1-3
    (let ([subset (take (shuffle pending) (min num-attest (length pending)))])
      (for-each (lambda (txn)
                  (let ([ans (generate-answer (find-question-by-id (transaction-question-id txn)) (node-archetype node))]
                        [t (current-inexact-milliseconds)]
                        [att-type "attestation"])
                    (let ([att-txn (create-txn (transaction-question-id txn) (node-pubkey node) ans t att-type)])
                      (set-node-mempool! node (cons att-txn (node-mempool node))))))
                subset))))

;; Meeting
(define (run-meeting)
  (let ([all-nodes (shuffle (append (hash-ref *app-db* 'class-a) (hash-ref *app-db* 'class-b)))]
        [past-pairs (make-hash)]) ; Track no repeats, but per week—stub for now
    (for ([i (in-range 0 (length all-nodes) 2)])
      (let ([node1 (list-ref all-nodes i)]
            [node2 (if (< (+ i 1) (length all-nodes)) (list-ref all-nodes (+ i 1)) #f)])
        (when node2
          (if (< (random) sync-failure-prob)
              (printf "Sync failed for ~a and ~a~%" (node-pubkey node1) (node-pubkey node2))
              (begin
                (sync-delta node1 node2)
                (sync-delta node2 node1)
                (attest-partner node1 node2)
                (attest-partner node2 node1)
                (propose-block node1)
                (propose-block node2))))))))

;; Sim Cycle
(define (is-meeting-day? day)
  (member (modulo day 7) '(1 3 5 6))) ; Tue, Thu, Fri, Sat

(define (run-sim num-days)
  (for ([day (in-range 1 (add1 num-days))])
    (run-day day)
    (if (is-meeting-day? day)
        (run-meeting)
        (printf "No meeting on day ~a.~%" day))
    (display-daily-stats day))
  (display-final-stats))

;; Stats
(define (display-daily-stats day)
  (let ([all-nodes (append (hash-ref *app-db* 'class-a) (hash-ref *app-db* 'class-b))])
    (printf "Day ~a Stats:\nTotal Txns: ~a\nBlocks Mined: ~a\nChain Fragmentation: ~a%~%"
            day
            (apply + (map (lambda (n) (length (node-mempool n))) all-nodes))
            (apply + (map (lambda (n) (length (node-chain n))) all-nodes))
            (calculate-fragmentation all-nodes))))

(define (calculate-fragmentation nodes)
  (let ([max-length (apply max (map (lambda (n) (length (node-chain n))) nodes))])
    (* 100 (/ (count (lambda (n) (< (length (node-chain n)) max-length)) nodes) total-nodes))))

(define (display-final-stats)
  (let ([all-nodes (append (hash-ref *app-db* 'class-a) (hash-ref *app-db* 'class-b))])
    (printf "Final Stats:\nTruth Accuracy: ~a%\nAvg Convergence Velocity: ~a meetings\nAvg Block Latency: ~a days\n"
            (calculate-truth-accuracy all-nodes)
            (calculate-conv-velocity all-nodes)
            (calculate-block-latency all-nodes))
    (plot-reputation-histogram all-nodes)))

;; Stub Stats Fns (expand in Step 4)
(define (calculate-truth-accuracy nodes) 85) ; % MCQ converged to answerKey
(define (calculate-conv-velocity nodes) 4) ; Mean meetings to mine
(define (calculate-block-latency nodes) 2) ; Mean days completion to mine
(define (plot-reputation-histogram nodes)
  (let ([reps (map (lambda (n) (length (node-chain n))) nodes)])
    (plot (discrete-histogram (map vector (range (length reps)) reps))
          #:title "Reputation Distribution" #:x-label "Node" #:y-label "Blocks Mined")))

;; Test in REPL
(run-sim 7) ; Week sim
(display-final-stats)
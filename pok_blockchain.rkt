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
                               (let ([qid (transaction-question-id txn)]
                                     (conv (if (string=? (question-qtype (find-question-by-id qid)) "frq")
                                               (calculate-frq-convergence qid)
                                               (calculate-convergence qid))))
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
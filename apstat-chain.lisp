(defpackage :apstat-chain
  (:use :cl :cl-json))
(in-package :apstat-chain)

;; Schemas as predicates (simpler than Malli for proto)
(defun valid-completion-txn-p (txn)
  (and (stringp (getf txn :question-id))
       (stringp (getf txn :owner-pub-key))
       (stringp (getf txn :answer-hash))
       (integerp (getf txn :timestamp))
       t))  ; Expand as needed

;; State (like app-db atom)
(defvar *app-db* (make-hash-table) "Central state hash-table")
(setf (gethash :curriculum *app-db*) nil)
(setf (gethash :mempool *app-db*) nil)
(setf (gethash :chain *app-db*) nil)
(setf (gethash :identity *app-db*) nil)

;; Pure Functions
(defun create-mcq-tx (question-id public-key answer-key)
  (let* ((digest (ironclad:digest-sequence :sha256 (sb-ext:string-to-octets answer-key)))
         (hash-hex (ironclad:byte-array-to-hex-string digest))
         (txn (list :tx-id (format nil "~a" (gensym "TX-"))
                    :timestamp (get-universal-time)
                    :owner-pub-key public-key
                    :question-id question-id
                    :payload (list :answer answer-key :answer-hash hash-hex))))
    (if (valid-completion-txn-p txn)
        txn
        (error "Invalid txn: ~a" txn))))

(defun add-tx-to-mempool (txn)
  (push txn (gethash :mempool *app-db*)))

(defun find-question-by-id (q-id)
  (find-if (lambda (q) (string= (getf q :id) q-id)) (gethash :curriculum *app-db*)))

(defun group-attestations (attns)  ; Stub: attns = list of txns
  (let ((dist (make-hash-table :test #'equal)))
    (dolist (attn attns dist)
      (incf (gethash (getf (getf attn :payload) :answer-hash) dist 0)))))

(defun calculate-convergence (question-id)
  (let* ((all-txns (append (gethash :mempool *app-db*) (loop for block in (gethash :chain *app-db*) append (getf block :txns))))
         (attns (remove-if-not (lambda (txn) (string= (getf txn :question-id) question-id)) all-txns))
         (dist (group-attestations attns))
         (total (reduce #'+ (alexandria:hash-table-values dist) :initial-value 0))
         (max-count (if (zerop (hash-table-count dist)) 0 (reduce #'max (alexandria:hash-table-values dist)))))
    (if (zerop total) 0 (/ max-count (float total)))))

(defun propose-block ()
  (let ((valid-txns (remove-if-not (lambda (txn) (>= (calculate-convergence (getf txn :question-id)) 0.8)) (gethash :mempool *app-db*)))  ; Quorum stub: 80% convergence
        (block (list :hash (format nil "~a" (gensym "BLOCK-")) :txns valid-txns)))
    (when valid-txns
      (push block (gethash :chain *app-db*))
      (setf (gethash :mempool *app-db*) (set-difference (gethash :mempool *app-db*) valid-txns :test #'equal))
      (format t "Block proposed: ~a~%" block))))

;; Effectful Orchestration
(defun generate-new-identity ()
  (list :public-key (format nil "pubkey-~a" (gensym))))

(defun init ()
  (setf (gethash :identity *app-db*) (generate-new-identity))
  (setf (gethash :curriculum *app-db*) (json:decode-json-from-source (open "curriculum.json")))  ; Load JSON
  (setf (gethash :mempool *app-db*) nil)
  (setf (gethash :chain *app-db*) nil)
  (format t "Initialized with ~a questions.~%" (length (gethash :curriculum *app-db*))))

(defun submit-mcq-answer (question-id answer-key)
  (let ((pubkey (getf (gethash :identity *app-db*) :public-key))
        (txn (create-mcq-tx question-id pubkey answer-key)))
    (add-tx-to-mempool txn)
    (format t "Txn added to mempool: ~a~%" txn)))

;; For persistence sim (save to file)
(defun save-state ()
  (with-open-file (out "state.json" :direction :output :if-exists :supersede)
    (json:encode-json *app-db* out)))

(defun load-state ()
  (with-open-file (in "state.json" :if-does-not-exist nil)
    (when in (setf *app-db* (json:decode-json in)))))
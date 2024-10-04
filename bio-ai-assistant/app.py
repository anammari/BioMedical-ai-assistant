import uuid

from flask import Flask, request, jsonify

from rag import rag

import db

app = Flask(__name__)

def initialize_database():
    db.init_db()

@app.route("/question", methods=["POST"])
def handle_question():
    data = request.json
    question = data["question"]

    if not question:
        return jsonify({"error": "No question provided"}), 400

    conversation_id = str(uuid.uuid4())

    answer_data = rag(question)

    result = {
        "conversation_id": conversation_id,
        "question": question,
        "answer": answer_data["answer"],
    }

    status = db.save_conversation(
            conversation_id=conversation_id,
            question=question,
            answer_data=answer_data,
        )

    if status:
        return jsonify(result)
    else:
        return jsonify({"error": "Conversation not saved"}), 400

@app.route("/feedback", methods=["POST"])
def handle_feedback():
    data = request.json
    conversation_id = data["conversation_id"]
    feedback = data["feedback"]

    if not conversation_id or feedback not in [1, -1]:
        return jsonify({"error": "Invalid input"}), 400

    status = db.save_feedback(
            conversation_id=conversation_id,
            feedback=feedback,
        )

    if status:
        result = {
            "message": f"Feedback received for conversation {conversation_id}: {feedback}"
        }
        return jsonify(result)
    else:
        result = {
            "error": f"Feedback not saved"
        }
        return jsonify(result), 400

if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)
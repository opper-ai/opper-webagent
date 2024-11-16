from flask import Flask, request, jsonify
from src.web_agent.main import navigate_with_ai

app = Flask(__name__)

# Example usage with curl:
# curl -X POST http://localhost:5000/navigate \
#   -H "Content-Type: application/json" \
#   -d '{"goal": "Log in to example.com", "secrets": "username: user, password: pass"}'

@app.route('/navigate', methods=['POST'])
def navigate():
    try:
        data = request.get_json()
        goal = data.get('goal')
        secrets = data.get('secrets')

        if not goal:
            return jsonify({'error': 'Goal is required'}), 400

        result = navigate_with_ai(goal, secrets)
        return jsonify({'result': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

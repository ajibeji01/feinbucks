from flask import Flask, render_template, request, jsonify
import json
import random
import os

app = Flask(__name__)

# Load user data
DATA_FILE = "passwords.json"
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def load_data(file=DATA_FILE):
    with open(file, "r") as f:
        return json.load(f)

def save_data(data, file=DATA_FILE):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

@app.route("/")
def home():
    return render_template("index.html")  # Now serving a proper HTML file

@app.route("/info/<user>", methods=["GET"])
def info(user):
    data = load_data()
    if user not in data:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"message": f"Test complete. Data found: F${data[user]['Feinbucks']}, Password: {data[user]['Password']}"})

@app.route("/signup", methods=["POST"])
def signup():
    data = load_data()
    req = request.json
    username = req.get("username")
    password = req.get("password")

    if username in data:
        return jsonify({"error": "Username already taken"}), 400

    if len(username) < 3 or len(username) > 20:
        return jsonify({"error": "Usernames must be between 3-20 characters"})

    data[username] = {"Password": password, "Notes": "", "Feinbucks": "0"}
    save_data(data)
    return jsonify({"message": "Signup successful"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = load_data()
    req = request.json
    username = req.get("username")
    password = req.get("password")

    if username not in data or data[username]["Password"] != password:
        return jsonify({"error": "Invalid username or password"}), 401

    return jsonify({
        "message": "Login successful",
        "Feinbucks": data[username]["Feinbucks"],
        "Notes": data[username]["Notes"]
    })

@app.route("/balance/<username>", methods=["GET"])
def get_balance(username):
    data = load_data()
    if username not in data:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"Feinbucks": data[username]["Feinbucks"]})

@app.route("/notes/<username>", methods=["GET", "POST"])
def manage_notes(username):
    data = load_data()
    if username not in data:
        return jsonify({"error": "User not found"}), 404

    if request.method == "GET":
        return jsonify({"Notes": data[username]["Notes"]})

    elif request.method == "POST":
        req = request.json
        new_notes = req.get("notes", "")
        data[username]["Notes"] = new_notes
        save_data(data)
        return jsonify({"message": "Notes updated successfully"})

@app.route("/gamble/<username>", methods=["POST"])
def gamble(username):
    data = load_data()
    if username not in data:
        return jsonify({"error": "User not found"}), 404

    req = request.json

    req_bet = req.get("bet", 0)  # Get the value from request, default to 0 if missing
    try:
        bet = float(req_bet) if str(req_bet).strip() else 0.0  # Convert to float, default to 0.0 if empty
    except ValueError:
        bet = 0.0  # Default to 0.0 if conversion fails
    feinbucks = float(data[username]["Feinbucks"])

    if bet <= 0:
        return jsonify({"error": "You must bet a positive amount"}), 400
    elif bet <= 0.01:
        return jsonify({"error": "You must bet at least 1 feincent"}), 400
    elif feinbucks < bet:
        return jsonify({"error": "You're too poor for this"}), 400

    data[username]["Feinbucks"] = str(feinbucks - bet)
    result = random.choices([0, 1.2, 1.5, 2], weights=[40, 30, 20, 10])[0]
    winnings = bet * result
    data[username]["Feinbucks"] = str(round(float(data[username]["Feinbucks"]) + winnings, 2))
    save_data(data)

    return jsonify({"result": result, "winnings": winnings})

@app.route("/claimCode/<username>", methods=["POST"])
def claimCode(username):
    data = load_data()
    code_data = load_data("codes.json")
    if username not in data:
        return jsonify({"error": "User not found"}), 404
    
    req = request.json
    
    code = req.get("code")
    if not code in code_data:
        return jsonify({"error": "Code not found"})

    if "owner" in code_data[code]:
        return jsonify({"error": f"Code was already claimed by {code_data[code]['owner']}"})

    code_data[code]["owner"] = username
    winnings = float(code_data[code]["winnings"])

    data[username]["Feinbucks"] = str(round(float(data[username]["Feinbucks"]) + winnings, 2))
    save_data(code_data, "codes.json")
    save_data(data)

    return jsonify({"winnings": winnings})


@app.route("/transfer/<username>", methods=["POST"])
def transfer(username):
    data = load_data()
    if username not in data:
        return jsonify({"error": "User not found"}), 404

    req = request.json

    req_amount = req.get("amount")

    if req_amount == "":
        return jsonify({"error": "Input an amount"})

    amount = float(req.get("amount"))
    recipient = req.get("recipient")

    if not recipient in data:
        return jsonify({"error": "Recipient not found"})

    if amount <= 0:
        return jsonify({"error": "You can only transfer a positive amount"})
    elif amount <= 0.01:
        return jsonify({"error": "You must transfer at least 1 feincent"})

    data[username]["Feinbucks"] = str(round(float(data[username]["Feinbucks"]) - amount, 2))
    data[recipient]["Feinbucks"] = str(round(float(data[recipient]["Feinbucks"]) + amount, 2))
    save_data(data)

    return jsonify({})

LIMITEDS_FILE = "limiteds.json"

def load_limiteds():
    if not os.path.exists(LIMITEDS_FILE):
        return {}
    with open(LIMITEDS_FILE, "r") as f:
        return json.load(f)

def save_limiteds(data):
    with open(LIMITEDS_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route("/marketplace/<username>", methods=["GET"])
def marketplace(username):
    print("Marketplace Backend Fired")
    data = load_limiteds()

    if not username:
        return jsonify({"error": "Username required"}), 400

    owned_limiteds = {}
    marketplace_limiteds = {}

    for limited_name, details in data.items():
        for copy, owner_data in details["owners"].items():
            if owner_data["name"] == username:
                owned_limiteds[limited_name] = {
                    "copy": copy,
                    "market": owner_data["market"]
                }
            if owner_data["market"]:
                if limited_name not in marketplace_limiteds:
                    marketplace_limiteds[limited_name] = []
                marketplace_limiteds[limited_name].append({
                    "copy": copy,
                    "seller": owner_data["name"],
                    "price": owner_data["market"]
                })
    print("Sending..")
    print({"owned": owned_limiteds, "market": marketplace_limiteds})
    return jsonify({"owned": owned_limiteds, "market": marketplace_limiteds})

@app.route("/sell_limited", methods=["POST"])
def sell_limited():
    data = load_limiteds()
    req = request.json
    username = req.get("username")
    limited_name = req.get("limited")
    price = req.get("price")

    if not username or not limited_name or not price:
        return jsonify({"error": "Invalid request"}), 400

    if limited_name not in data:
        return jsonify({"error": "Limited does not exist"}), 404

    for owner_id, owner_data in data[limited_name]["owners"].items():
        if owner_data["name"] == username:
            owner_data["market"] = price
            save_limiteds(data)
            return jsonify({"success": True})

    return jsonify({"error": "You do not own this limited"}), 403

@app.route("/buy_limited", methods=["POST"])
def buy_limited():
    data = load_limiteds()
    req = request.json
    username = req.get("username")
    limited_name = req.get("limited")
    seller = req.get("seller")
    price = req.get("price")

    if not username or not limited_name or not seller or not price:
        return jsonify({"error": "Invalid request"}), 400

    if limited_name not in data:
        return jsonify({"error": "Limited does not exist"}), 404

    for owner_id, owner_data in data[limited_name]["owners"].items():
        if owner_data["name"] == seller and owner_data["market"] == str(price):
            # Transfer ownership
            owner_data["market"] = ""
            owner_data["name"] = username
            save_limiteds(data)
            return jsonify({"success": True})

    return jsonify({"error": "Limited is no longer available"}), 404





if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

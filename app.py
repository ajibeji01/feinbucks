from flask import Flask, render_template, request, jsonify
import json
import random
import os
import requests
import threading
import time

DISCORD_BACKUP_WEBHOOK_URL = "https://discord.com/api/webhooks/1344040756263915580/2XZ5MdnNZW01khNcaMQCzNeMv9hzZuLFxavURFwHakFePK1N4GbOhW8CK2xaRw8DcL79"
DISCORD_ACTION_WEBHOOK_URL = "https://discord.com/api/webhooks/1344205724343074826/SLjrdf7cMwW-kFngyTnyS2Tn0FTmphrwk8Ub_fC1Xpaa_pA_DChsOAiCHkjaw8YEOZo7"

last_backup = time.time()
def send_backup(string, file):
    if time.time() - last_backup < 300:
        return
    last_backup = time.time()
    formatted =\
f"""**NEW LOG**
for *{file}*
```
{string}
```
"""
    response = requests.post(DISCORD_BACKUP_WEBHOOK_URL, json={"content": formatted})

def log_action(string):
    formatted =\
f"""## NEW ACTION
> {string}
"""
    response = requests.post(DISCORD_ACTION_WEBHOOK_URL, json={"content": formatted})

app = Flask(__name__)

# Load user data
DATA_FILE = "passwords.json"
LIMITEDS_FILE = "limiteds.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def load_data(file=DATA_FILE):
    with open(file, "r") as f:
        return json.load(f)

def save_data(data, file=DATA_FILE):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)
        threading.Thread(target=send_backup, args=[json.dumps(data, indent=4), file]).start()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/info/<user>", methods=["GET"])
def info(user):
    data = load_data()
    if user not in data:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"message": f"Test complete. Data found: F${data[user]['Feinbucks']}, Password: {data[user]['Password']}"})

@app.route("/signup", methods=["POST"])
def signup():
    allowed_characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"

    data = load_data()
    req = request.json
    username = req.get("username")
    password = req.get("password")

    for c in username:
        if c not in allowed_characters:
            return jsonify({"error": f"'{c}' is a disallowed character"})

    if username in data:
        return jsonify({"error": "Username already taken"}), 400

    if len(username) < 3 or len(username) > 20:
        return jsonify({"error": "Usernames must be between 3-20 characters"})

    data[username] = {"Password": password, "Feinbucks": "0"}
    save_data(data)
    threading.Thread(target=log_action,
                     args=[f"**New account created:** Username: **{username}** Password: ||**{password}**||"]).start()
    return jsonify({"message": "Signup successful"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = load_data()
    req = request.json
    username = req.get("username")
    password = req.get("password")

    if username not in data or data[username]["Password"] != password:
        return jsonify({"error": "Invalid username or password"}), 401

    threading.Thread(target=log_action,
                     args=[f"**{username}** logged in to their account."]).start()

    return jsonify({
        "message": "Login successful",
        "Feinbucks": data[username]["Feinbucks"]
    })

@app.route("/balance/<username>", methods=["GET"])
def get_balance(username):
    data = load_data()
    if username not in data:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"Feinbucks": data[username]["Feinbucks"]})

@app.route("/changePassword/<username>", methods=["POST"])
def change_password(username):
    data = load_data()
    if username not in data:
        return jsonify({"error": "User not found"}), 404

    req = request.json
    old = req.get("old")
    new = req.get("New")

    if old != data[username]["Password"]:
        return jsonify({"error": "Incorrect original password"})

    data[username]["Password"] = new
    save_data(data)
    threading.Thread(target=log_action,
                     args=[f"**{username}** changed their password: Old: ||**{old}**|| New: ||**{new}**||"]).start()

    return jsonify({})

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
    elif bet < 0.01:
        return jsonify({"error": "You must bet at least 1 feincent"}), 400
    elif feinbucks < bet:
        return jsonify({"error": "You're too poor for this"}), 400

    data[username]["Feinbucks"] = str(feinbucks - bet)
    result = random.choices([0, 1.2, 1.5, 2], weights=[40, 30, 20, 10])[0]
    winnings = bet * result
    data[username]["Feinbucks"] = str(round(float(data[username]["Feinbucks"]) + winnings, 2))
    save_data(data)
    threading.Thread(target=log_action,
                     args=[f"**{username}** gambled some feinbucks: Bet: **{bet}** Winnings: **{winnings}** Profit: **{str(winnings-bet)}**"]).start()

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
    threading.Thread(target=log_action,
                     args=[f"**{username}** claimed a code: Code: **{code}** Winnings: **{winnings}**"]).start()

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
    elif amount < 0.01:
        return jsonify({"error": "You must transfer at least 1 feincent"})
    elif amount > float(data[username]["Feinbucks"]):
        return jsonify({"error": "You don't have enough feinbucks for that >:)"})

    data[username]["Feinbucks"] = str(round(float(data[username]["Feinbucks"]) - amount, 2))
    data[recipient]["Feinbucks"] = str(round(float(data[recipient]["Feinbucks"]) + amount, 2))
    save_data(data)
    threading.Thread(target=log_action,
                     args=[f"**{username}** transfered **{amount}** feinbucks to **{recipient}**."]).start()

    return jsonify({})


@app.route("/marketplace/<username>", methods=["GET"])
def marketplace(username):
    data = load_data(LIMITEDS_FILE)

    if not username:
        return jsonify({"error": "Username required"}), 400

    owned_limiteds = {}
    marketplace_limiteds = {}

    for limited_name, details in data.items():
        for copy, owner_data in details["owners"].items():
            if owner_data["name"] == username:
                if limited_name not in owned_limiteds:
                    owned_limiteds[limited_name] = []
                owned_limiteds[limited_name].append({
                    "copy": copy,
                    "market": owner_data["market"]
                })
            if owner_data["market"]:
                if limited_name not in marketplace_limiteds:
                    marketplace_limiteds[limited_name] = []
                marketplace_limiteds[limited_name].append({
                    "copy": copy,
                    "seller": owner_data["name"],
                    "price": owner_data["market"]
                })

        if int(details["copies"]) > len(details["owners"]):
            if limited_name not in marketplace_limiteds:
                marketplace_limiteds[limited_name] = []
            marketplace_limiteds[limited_name].append({
                "copy": str(len(details["owners"])+1),
                "seller": "Feinbank",
                "price": details["price"]
            })

    return jsonify({"owned": owned_limiteds, "market": marketplace_limiteds})

@app.route("/sell_limited", methods=["POST"])
def sell_limited():
    data = load_data(LIMITEDS_FILE)
    req = request.json
    username = req.get("username")
    limited_name = req.get("limited")
    price = req.get("price")
    limited_copy = req.get("copy")

    if not username or not limited_name:
        return jsonify({"error": "Invalid request"}), 400

    if limited_name not in data:
        return jsonify({"error": "Limited does not exist"}), 404

    if username != data[limited_name]["owners"][limited_copy]["name"]:
        return jsonify({"error": "You do not own this limited"}), 403

    owner_data = data[limited_name]["owners"][limited_copy]
    owner_data["market"] = price
    save_data(data, LIMITEDS_FILE)
    threading.Thread(target=log_action,
                     args=[f"**{username}** put their **{limited_name} #{limited_copy}** on the market for **{price}** feinbucks."]).start()

    return jsonify({"success": True})



@app.route("/buy_limited", methods=["POST"])
def buy_limited():
    data = load_data()
    limited_data = load_data(LIMITEDS_FILE)
    req = request.json
    username = req.get("username")
    limited_name = req.get("limited")
    limited_copy = req.get("copy")
    seller = req.get("seller")
    price = req.get("price")

    if not username or not limited_name or not seller or not price:
        return jsonify({"error": "Invalid request"}), 400

    if limited_name not in limited_data:
        return jsonify({"error": "Limited does not exist"}), 404




    # Validate Transaction
    if float(data[username]["Feinbucks"]) < float(price):
        return jsonify({"error": "You are too poor to buy this limited"})


    # Transfer ownership
    # if limited_copy in limited_data[limited_name]["owners"]:                               # If buying off a player
    if seller != "Feinbank":

        if not limited_data[limited_name]["owners"][limited_copy]["market"]:
            return jsonify({"error": "Limited is no longer for sale. Refresh limiteds page"}), 404

        data[username]["Feinbucks"] = str(round(float(data[username]["Feinbucks"]) - price, 2))
        data[seller]["Feinbucks"] = str(round(float(data[seller]["Feinbucks"]) + price, 2))
        copy_data = limited_data[limited_name]["owners"][limited_copy]
        copy_data["market"] = ""
        copy_data["name"] = username
    else:                                                                                  # If buying off the bank
        if len(limited_data[limited_name]["owners"]) >= int(limited_copy):
            return jsonify({"error": "Someone already bought that copy. Refresh limiteds page."}), 404

        data[username]["Feinbucks"] = str(round(float(data[username]["Feinbucks"]) - price, 2))
        limited_data[limited_name]["owners"][limited_copy] = {
            "name": username,
            "market": ""
        }

    save_data(limited_data, LIMITEDS_FILE)
    save_data(data)
    threading.Thread(target=log_action,
                     args=[f"**{username}** bought **{limited_name} #{limited_copy}** from **{seller}** for **{price}** feinbucks."]).start()

    return jsonify({"success": True})

    return jsonify({"error": "Limited is no longer available"}), 404





if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

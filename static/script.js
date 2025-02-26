let loggedInUser = "";

function logout() {
    dashboard()

    document.getElementById("login_block").style.display = "block";

    document.getElementById("balance_block").style.display = "none";
    document.getElementById("action_block").style.display = "none";
    document.getElementById("logout_block").style.display = "none";

    document.getElementById("username").value = "";
    document.getElementById("password").value = "";

    document.getElementById("loginResult").innerText  = "";

    loggedInUser = "";
}

function dashboard() {
    document.getElementById("login_block").style.display = "none";

    document.getElementById("password_block").style.display = "none";
    document.getElementById("gamble_block").style.display = "none";
    document.getElementById("codes_block").style.display = "none";
    document.getElementById("transfer_block").style.display = "none";
    document.getElementById("marketplace").style.display = "none";

    document.getElementById("balance_block").style.display = "block";
    document.getElementById("action_block").style.display = "block";


    document.getElementById("logout_block").style.display = "block";
}

function login() {
    let username = document.getElementById("username").value;
    let password = document.getElementById("password").value;

    fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            document.getElementById("loginResult").innerText = data.error;
        } else {
            loggedInUser = username;
            dashboard()
            document.getElementById("welcome").innerText = "Welcome back, " + loggedInUser;
            document.getElementById("balance").innerText = "Balance: F$" + data.Feinbucks;
        }
    });
}

function signup() {
    let username = document.getElementById("username").value;
    let password = document.getElementById("password").value;

    fetch("/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            document.getElementById("loginResult").innerText = data.error;
        } else {
            login()
        }

    });
}

function getBalance() {
    if (!loggedInUser) {
        alert("Please log in first!");
        return;
    }

    fetch(`/balance/${loggedInUser}`)
    .then(res => res.json())
    .then(data => document.getElementById("balance").innerText = "Balance: F$" + data.Feinbucks);
}

function changePassword() {
    if (!loggedInUser) {
        alert("Please log in first!");
        return;
    }

    let old = document.getElementById("old_password").value;
    let New = document.getElementById("new_password").value;
    let new_confirm = document.getElementById("confirm_new_password").value;

    if (New != new_confirm) {
        document.getElementById("passwordResult").innerText = "New passwords don't match";
        document.getElementById("passwordResult").style.color = "rgb(200,0,0)";
        return;
    }

    fetch(`/changePassword/${loggedInUser}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ old, New })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            document.getElementById("passwordResult").innerText = data.error;
            document.getElementById("passwordResult").style.color = "rgb(200,0,0)";
        } else {
            document.getElementById("passwordResult").innerText = "Successfully updated password";
            document.getElementById("passwordResult").style.color = "rgb(0,0,0)";
        }
    });
}

function gamble() {
    if (!loggedInUser) {
        alert("Please log in first!");
        return;
    }

    let bet = document.getElementById("bet").value;
    fetch(`/gamble/${loggedInUser}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bet })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            document.getElementById("gambleResult").innerText = data.error;
            document.getElementById("gambleResult").style.color = "rgb(200,0,0)";
        } else {
            document.getElementById("gambleResult").innerText = "You won: F$" + data.winnings;
            document.getElementById("gambleResult").style.color = "rgb(0,0,0)";
            getBalance();
        }
    });
}

function claimCode() {
        if (!loggedInUser) {
        alert("Please log in first!");
        return;
    }

    let code = document.getElementById("code").value;

    fetch(`/claimCode/${loggedInUser}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            document.getElementById("codeResult").innerText = data.error;
            document.getElementById("codeResult").style.color = "rgb(200,0,0)";
        } else {
            document.getElementById("codeResult").innerText = "Code claimed +F$" + data.winnings;
            document.getElementById("codeResult").style.color = "rgb(0,0,0)";
            getBalance();
        }
    });
}

function transfer() {
        if (!loggedInUser) {
        alert("Please log in first!");
        return;
    }

    let amount = document.getElementById("transferAmount").value;
    let recipient = document.getElementById("recipient").value;

    fetch(`/transfer/${loggedInUser}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount, recipient })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            document.getElementById("transferResult").innerText = data.error;
            document.getElementById("transferResult").style.color = "rgb(200,0,0)";
        } else {
            document.getElementById("transferResult").innerText = "Successfully transfered feinbucks";
            document.getElementById("transferResult").style.color = "rgb(0,0,0)";
            getBalance();
        }
    });
}

function loadMarketplace() {


    fetch(`/marketplace/${loggedInUser}`)
    .then(res => res.json())
    .then(data => {

        // Populate owned limiteds
        const ownedTable = document.getElementById("owned-limiteds");
        ownedTable.innerHTML = "";

        for (const [limited, owned] of Object.entries(data.owned)) {
            owned.forEach(details => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${limited}</td>
                    <td>#${details.copy}</td>
                    <td>${details.market ? `F$${details.market}` : "Not for sale"}</td>
                    <td>
                        <input type="number" id="sell-price-${limited}-${details.copy}" placeholder="Enter price">
                        <button onclick="sellLimited('${limited}', '${details.copy}')">Sell</button>
                        <button onclick="takeOffLimited('${limited}', '${details.copy}')">Take Off</button>
                    </td>
                `;
                ownedTable.appendChild(row);
            })
        }

        // Populate marketplace limiteds
        const marketTable = document.getElementById("marketplace-list");
        marketTable.innerHTML = "";

        for (const [limited, sales] of Object.entries(data.market)) {
            sales.forEach(sale => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${limited}</td>
                    <td>#${sale.copy}</td>
                    <td>${sale.seller}</td>
                    <td>F$${sale.price}</td>
                    <td><button onclick="buyLimited('${limited}', '${sale.copy}', '${sale.seller}', ${sale.price})">Buy</button></td>
                `;
                marketTable.appendChild(row);
            });
        }
    });
}

async function sellLimited(limitedName, limitedCopy) {
    const price = document.getElementById(`sell-price-${limitedName}-${limitedCopy}`).value;

    if (!price || isNaN(price) || price <= 0) {
        document.getElementById("marketResult").innerText = "Enter a valid price";
        document.getElementById("marketResult").style.color = "rgb(200,0,0)";
        return;
    }

    const response = await fetch("/sell_limited", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: loggedInUser, limited: limitedName, copy: limitedCopy, price })
    });

    const data = await response.json();
    if (data.success) {
        document.getElementById("marketResult").innerText = "Limited listed for sale";
        document.getElementById("marketResult").style.color = "rgb(0,0,0)";
        loadMarketplace();
    } else {
        document.getElementById("marketResult").innerText = "Error: " + data.error;
        document.getElementById("marketResult").style.color = "rgb(200,0,0)";
    }
}

async function takeOffLimited(limitedName, limitedCopy) {

    const response = await fetch("/sell_limited", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: loggedInUser, limited: limitedName, copy: limitedCopy, price: "" })
    });

    const data = await response.json();
    if (data.success) {
        document.getElementById("marketResult").innerText = "Limited taken off marketplace";
        document.getElementById("marketResult").style.color = "rgb(0,0,0)";
        loadMarketplace();
    } else {
        document.getElementById("marketResult").innerText = data.error;
        document.getElementById("marketResult").style.color = "rgb(200,0,0)";
    }
}

async function buyLimited(limitedName, limitedCopy, seller, price) {
    const response = await fetch("/buy_limited", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: loggedInUser, limited: limitedName, copy: limitedCopy, seller, price })
    });

    const data = await response.json();
    if (data.success) {
        document.getElementById("marketResult").innerText = "Limited bought successfully";
        document.getElementById("marketResult").style.color = "rgb(0,0,0)";
        loadMarketplace();
        getBalance();
    } else {
        document.getElementById("marketResult").innerText = data.error;
        document.getElementById("marketResult").style.color = "rgb(200,0,0)";
    }
}

function passwordUI() {
    if (!loggedInUser) {
        alert("Please log in first!");
        return;
    }
    dashboard()
    document.getElementById("password_block").style.display = "block";
}

function gambleUI() {
    if (!loggedInUser) {
        alert("Please log in first!");
        return;
    }
    dashboard()
    document.getElementById("gamble_block").style.display = "block";
}

function codesUI() {
    if (!loggedInUser) {
        alert("Please log in first!");
        return;
    }
    dashboard()
    document.getElementById("codes_block").style.display = "block";
}

function transferUI() {
    if (!loggedInUser) {
        alert("Please log in first!");
        return;
    }
    dashboard()
    document.getElementById("transfer_block").style.display = "block";
}

function limitedsUI() {
    if (!loggedInUser) {
        alert("Please log in first!");
        return;
    }
    dashboard()
    document.getElementById("marketplace").style.display = "block";
    loadMarketplace()
}

from web3 import Web3

# Connect to Ganache (your local private Ethereum blockchain)
ganache_url = "http://127.0.0.1:7545"
web3 = Web3(Web3.HTTPProvider(ganache_url))

# Check connection
if web3.is_connected():
    print("[✓] Connected to Ethereum network")
else:
    print("[x] Connection failed")

# Replace with your deployed contract address from Truffle migration output
contract_address = "0x5b6694796d3b9d9e5bAFEEa503bfA8A6FEad4Bf5"

# Paste your ABI here
abi = [
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "id",
          "type": "uint256"
        },
        {
          "indexed": False,
          "internalType": "string",
          "name": "userId",
          "type": "string"
        },
        {
          "indexed": False,
          "internalType": "string",
          "name": "description",
          "type": "string"
        },
        {
          "indexed": False,
          "internalType": "string",
          "name": "riskLevel",
          "type": "string"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "timestamp",
          "type": "uint256"
        }
      ],
      "name": "AlertRecorded",
      "type": "event"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "name": "alerts",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "id",
          "type": "uint256"
        },
        {
          "internalType": "string",
          "name": "userId",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "description",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "riskLevel",
          "type": "string"
        },
        {
          "internalType": "uint256",
          "name": "timestamp",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "string",
          "name": "_userId",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "_description",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "_riskLevel",
          "type": "string"
        }
      ],
      "name": "recordAlert",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "getAllAlerts",
      "outputs": [
        {
          "components": [
            {
              "internalType": "uint256",
              "name": "id",
              "type": "uint256"
            },
            {
              "internalType": "string",
              "name": "userId",
              "type": "string"
            },
            {
              "internalType": "string",
              "name": "description",
              "type": "string"
            },
            {
              "internalType": "string",
              "name": "riskLevel",
              "type": "string"
            },
            {
              "internalType": "uint256",
              "name": "timestamp",
              "type": "uint256"
            }
          ],
          "internalType": "struct AlertStorage.Alert[]",
          "name": "",
          "type": "tuple[]"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    }
]

# Connect to the deployed contract
contract = web3.eth.contract(address=contract_address, abi=abi)

# Pick an account from Ganache
account = web3.eth.accounts[0]

# Send a test alert
tx_hash = contract.functions.recordAlert(
    "user123", 
    "Multiple failed login attempts detected", 
    "High"
).transact({'from': account})

# Wait for confirmation
web3.eth.wait_for_transaction_receipt(tx_hash)
print("[✓] Alert recorded successfully on blockchain!")

# Fetch all alerts
alerts = contract.functions.getAllAlerts().call()
print("[+] Blockchain Alert Records:")
for alert in alerts:
    print(alert)

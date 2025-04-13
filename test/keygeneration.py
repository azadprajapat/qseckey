from qseckey import initialize,register_connection,get_key

initialize()
result = register_connection({
  "source_KME_ID": "sender_app",
  "target_KME_ID": "receiver_app",
  "master_SAE_ID": "ghi",
  "slave_SAE_ID": "jk3"
})
print(result)
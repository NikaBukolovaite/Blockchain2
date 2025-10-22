from Crypto.Cipher import AES

# AES-hash parametrai
BLOCK = 16
IV_LEFT = bytes.fromhex("0123456789abcdeffedcba9876543210")
IV_RIGHT = bytes.fromhex("fedcba98765432100123456789abcdef")
FINAL_CONST = bytes.fromhex('ffffffffffffffffffffffffffffffff')

def pad_message(message: bytes) -> bytes:
    L = len(message)
    message_in_bits = L * 8
    padded = message + b'\x80'
    num_of_zeros = (16 - (len(padded) + 8) % 16) % 16
    padded += b'\x00' * num_of_zeros
    padded += message_in_bits.to_bytes(8, 'big')
    return padded

def xor_bytes(a: bytes, b: bytes) -> bytes:
    if len(a) != len(b):
        raise ValueError("Ilgiai turi sutapti")
    return bytes([x ^ y for x, y in zip(a, b)])

def aes_hashing(message: bytes) -> bytes:
    state_left = IV_LEFT
    state_right = IV_RIGHT
    padded_message = pad_message(message)

    for i in range(0, len(padded_message), BLOCK):
        Mi = padded_message[i:i + BLOCK]

        cipher = AES.new(state_left, AES.MODE_ECB)
        encrypted = cipher.encrypt(state_right)

        state_right = xor_bytes(encrypted, Mi)
        state_left, state_right = state_right, state_left

    cipher = AES.new(state_left, AES.MODE_ECB)
    final_enc = cipher.encrypt(FINAL_CONST)

    return final_enc

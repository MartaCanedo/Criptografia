from Crypto.Cipher import AES, ChaCha20_Poly1305, DES3
from Crypto.Random import get_random_bytes
from Crypto.Hash import HMAC, SHA256

BLOCK_SIZE = 16  # AES block size em bytes


def gen_key(bits=256):
	if bits not in (128, 192, 256):
		raise ValueError("bits must be 128, 192 or 256")
	return get_random_bytes(bits // 8)


def gen_iv():
	return get_random_bytes(BLOCK_SIZE)


def pad_pkcs7(data: bytes) -> bytes:
	pad_len = BLOCK_SIZE - (len(data) % BLOCK_SIZE)
	return data + bytes([pad_len]) * pad_len


def unpad_pkcs7(data: bytes) -> bytes:
	if not data:
		raise ValueError("Invalid padding (empty data)")
	pad_len = data[-1]
	if pad_len < 1 or pad_len > BLOCK_SIZE:
		raise ValueError("Invalid padding length")
	if data[-pad_len:] != bytes([pad_len]) * pad_len:
		raise ValueError("Invalid padding bytes")
	return data[:-pad_len]


def _get_keys(key: bytes):
	"""Return tuple (aes_key, hmac_key).

	Uses the provided key as AES key and first half as HMAC key.
	"""
	key_size = len(key)
	if key_size not in (16, 24, 32):
		raise ValueError(f"Invalid key size: {key_size*8} bits. Must be 128, 192, or 256.")

	aes_key = key
	hmac_key = key[: key_size // 2]
	return aes_key, hmac_key


def encrypt_cbc(key: bytes, plaintext: bytes) -> dict:
	aes_key, hmac_key = _get_keys(key)
	iv = gen_iv()
	cipher = AES.new(aes_key, AES.MODE_CBC, iv=iv)
	pt_padded = pad_pkcs7(plaintext)
	ciphertext = cipher.encrypt(pt_padded)
	h = HMAC.new(hmac_key, digestmod=SHA256)
	h.update(iv + ciphertext)
	tag = h.digest()
	return {"mode": "CBC", "iv": iv, "ciphertext": ciphertext, "tag": tag}


def decrypt_cbc(key: bytes, iv: bytes, ciphertext: bytes, tag: bytes) -> bytes:
	aes_key, hmac_key = _get_keys(key)
	h = HMAC.new(hmac_key, digestmod=SHA256)
	h.update(iv + ciphertext)
	try:
		h.verify(tag)
	except ValueError:
		raise ValueError("HMAC verification failed")
	cipher = AES.new(aes_key, AES.MODE_CBC, iv=iv)
	pt_padded = cipher.decrypt(ciphertext)
	return unpad_pkcs7(pt_padded)


def encrypt_ctr(key: bytes, plaintext: bytes) -> dict:
	aes_key, hmac_key = _get_keys(key)
	nonce = get_random_bytes(8)  # usar um nonce de 64 bits
	cipher = AES.new(aes_key, AES.MODE_CTR, nonce=nonce)
	ciphertext = cipher.encrypt(plaintext)
	h = HMAC.new(hmac_key, digestmod=SHA256)
	h.update(nonce + ciphertext)
	tag = h.digest()
	return {"mode": "CTR", "nonce": nonce, "ciphertext": ciphertext, "tag": tag}


def decrypt_ctr(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes) -> bytes:
	aes_key, hmac_key = _get_keys(key)
	h = HMAC.new(hmac_key, digestmod=SHA256)
	h.update(nonce + ciphertext)
	try:
		h.verify(tag)
	except ValueError:
		raise ValueError("HMAC verification failed")
	cipher = AES.new(aes_key, AES.MODE_CTR, nonce=nonce)
	return cipher.decrypt(ciphertext)


def encrypt_gcm(key: bytes, plaintext: bytes, aad: bytes = None) -> dict:
	nonce = get_random_bytes(12)  # recomendado 96-bit nonce para GCM
	cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
	if aad:
		cipher.update(aad)
	ciphertext, tag = cipher.encrypt_and_digest(plaintext)
	return {"mode": "GCM", "nonce": nonce, "ciphertext": ciphertext, "tag": tag, "aad": aad}


def decrypt_gcm(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes, aad: bytes = None) -> bytes:
	cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
	if aad:
		cipher.update(aad)
	try:
		plaintext = cipher.decrypt_and_verify(ciphertext, tag)
		return plaintext
	except ValueError:
		raise ValueError("Decifragem GCM falhou (Chave ou Tag incorreta)")


# --- ChaCha20-Poly1305 ---
def encrypt_chacha20(key: bytes, plaintext: bytes) -> dict:
	# ChaCha20 usa chaves de 256 bits (32 bytes)
	if len(key) != 32:
		# Ajuste simples para fins de benchmark se a chave for menor
		key = key.ljust(32, b'\0')[:32]
	cipher = ChaCha20_Poly1305.new(key=key)
	ciphertext, tag = cipher.encrypt_and_digest(plaintext)
	# Use an uppercase, canonical mode name so headers are consistent
	return {"mode": "CHACHA20", "nonce": cipher.nonce, "ciphertext": ciphertext, "tag": tag}


def decrypt_chacha20(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes) -> bytes:
	if len(key) != 32:
		key = key.ljust(32, b'\0')[:32]
	cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)
	return cipher.decrypt_and_verify(ciphertext, tag)


# --- Triple DES (3DES) ---
def encrypt_3des(key: bytes, plaintext: bytes) -> dict:
	# 3DES usa chaves de 16 ou 24 bytes
	key_3des = key[:24].ljust(24, b'\0')
	iv = get_random_bytes(8)  # Bloco do DES é 8 bytes
	cipher = DES3.new(key_3des, DES3.MODE_CBC, iv=iv)

	# Padding manual (PKCS7 para bloco de 8)
	pad_len = 8 - (len(plaintext) % 8)
	pt_padded = plaintext + bytes([pad_len]) * pad_len

	ciphertext = cipher.encrypt(pt_padded)
	return {"mode": "3DES", "iv": iv, "ciphertext": ciphertext}


def decrypt_3des(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
	key_3des = key[:24].ljust(24, b'\0')
	cipher = DES3.new(key_3des, DES3.MODE_CBC, iv=iv)
	pt_padded = cipher.decrypt(ciphertext)
	pad_len = pt_padded[-1]
	return pt_padded[:-pad_len]
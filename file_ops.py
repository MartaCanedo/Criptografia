# Operações de ficheiro: cifrar/decifrar ficheiros com suporte a AES, ChaCha20 e 3DES.

import os
import time
import json
from crypto_utils import (
    encrypt_cbc, decrypt_cbc, 
    encrypt_ctr, decrypt_ctr, 
    encrypt_gcm, decrypt_gcm,
    encrypt_chacha20, decrypt_chacha20,
    encrypt_3des, decrypt_3des
)

def encrypt_file(path_in: str, path_out: str, key: bytes, mode: str='GCM'):
    """Lê um ficheiro, cifra-o e guarda o resultado com um header JSON de metadados."""
    start = time.time()
    
    with open(path_in, 'rb') as fin:
        plaintext = fin.read()

    mode_upper = mode.upper()
    
    # Seleção do algoritmo com base no modo
    if mode_upper == 'GCM':
        res = encrypt_gcm(key, plaintext)
    elif mode_upper == 'CBC':
        res = encrypt_cbc(key, plaintext)
    elif mode_upper == 'CTR':
        res = encrypt_ctr(key, plaintext)
    elif mode_upper == 'CHACHA20':
        res = encrypt_chacha20(key, plaintext)
    elif mode_upper == '3DES':
        res = encrypt_3des(key, plaintext)
    else:
        raise ValueError(f"Modo {mode} não suportado")

    # Guardar ficheiro cifrado + metadados no header
    with open(path_out, 'wb') as fout:
        header = {
            'mode': res.get('mode'),
            'iv': res.get('iv').hex() if res.get('iv') else None,
            'nonce': res.get('nonce').hex() if res.get('nonce') else None,
            'tag': res.get('tag').hex() if res.get('tag') else None,
            'aad': res.get('aad').hex() if res.get('aad') else None
        }
        header_bytes = (json.dumps(header) + '\n').encode('utf-8')
        fout.write(header_bytes)
        fout.write(res['ciphertext'])
        
    elapsed = time.time() - start

    return {
        'file_in': path_in,
        'file_out': path_out,
        'mode': mode,
        'elapsed_s': elapsed,
        # incluir header + ciphertext no tamanho
        'ciphertext_len': len(header_bytes) + len(res['ciphertext'])
    }


def decrypt_file(path_in: str, path_out: str, key: bytes):
    """Lê o header JSON de um ficheiro e utiliza os metadados para o decifrar."""
    start = time.time()
    
    with open(path_in, 'rb') as fin:
        header_line = fin.readline()
        header = json.loads(header_line.decode('utf-8'))
        ciphertext = fin.read()
    
    mode = header.get('mode')
    mode_upper = (mode or '').upper()
    
    try:
        if mode_upper == 'GCM':
            nonce = bytes.fromhex(header['nonce'])
            tag = bytes.fromhex(header['tag'])
            aad = bytes.fromhex(header['aad']) if header.get('aad') else None
            plaintext = decrypt_gcm(key, nonce, ciphertext, tag, aad)
            
        elif mode_upper == 'CBC':
            iv = bytes.fromhex(header['iv'])
            tag = bytes.fromhex(header['tag'])
            plaintext = decrypt_cbc(key, iv, ciphertext, tag)
            
        elif mode_upper == 'CTR':
            nonce = bytes.fromhex(header['nonce'])
            tag = bytes.fromhex(header['tag'])
            plaintext = decrypt_ctr(key, nonce, ciphertext, tag)
            
        elif mode_upper == 'CHACHA20':
            nonce = bytes.fromhex(header['nonce'])
            tag = bytes.fromhex(header['tag'])
            plaintext = decrypt_chacha20(key, nonce, ciphertext, tag)
            
        elif mode_upper == '3DES':
            iv = bytes.fromhex(header['iv'])
            plaintext = decrypt_3des(key, iv, ciphertext)
            
        else:
            raise ValueError(f"Modo no ficheiro desconhecido: {mode}")
            
    except Exception as e:
        raise ValueError(f"Falha na decifragem: {str(e)}")

    with open(path_out, 'wb') as fout:
        fout.write(plaintext)
        
    elapsed = time.time() - start
    return {
        'file_in': path_in, 
        'file_out': path_out, 
        'elapsed_s': elapsed, 
        'plaintext_len': len(plaintext)
    }
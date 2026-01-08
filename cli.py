# CLI simples para cifrar/decifrar ficheiros e mensagens

import argparse
from aes_utils import gen_key, encrypt_gcm, decrypt_gcm
from file_ops import encrypt_file, decrypt_file
import os

def main():
    parser = argparse.ArgumentParser(description="AES util - cifrar/decifrar ficheiros")
    sub = parser.add_subparsers(dest='cmd')

    enc = sub.add_parser('encfile')
    enc.add_argument('infile')
    enc.add_argument('outfile')
    enc.add_argument('--mode', default='GCM', choices=['GCM','CBC','CTR'])
    enc.add_argument('--keyfile', default='key.bin')

    dec = sub.add_parser('decfile')
    dec.add_argument('infile')
    dec.add_argument('outfile')
    dec.add_argument('--keyfile', default='key.bin')

    args = parser.parse_args()

    if args.cmd == 'encfile':
        if not os.path.exists(args.keyfile):
            key = gen_key(256)
            with open(args.keyfile, 'wb') as kf:
                kf.write(key)
            print(f"Key gerada e escrita em {args.keyfile}")
        else:
            with open(args.keyfile, 'rb') as kf:
                key = kf.read()
        res = encrypt_file(args.infile, args.outfile, key, mode=args.mode)
        print("Encriptação feita:", res)
    elif args.cmd == 'decfile':
        with open(args.keyfile, 'rb') as kf:
            key = kf.read()
        res = decrypt_file(args.infile, args.outfile, key)
        print("Decifração concluída:", res)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

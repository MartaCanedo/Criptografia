# benchmark.py
# Executa medidas simples de desempenho para vários modos e tamanhos de chave.

import os
import csv
import time
import psutil
import gc
import threading

from crypto_utils import gen_key
from file_ops import encrypt_file, decrypt_file

TEST_FILE = 'test_large.bin'

def make_test_file(size_mb=10):

    #Cria ficheiro de teste com dados aleatórios.
    print(f"Criando ficheiro de teste de {size_mb} MB...")
    with open(TEST_FILE, 'wb') as f:
        # Escrever em blocos de 10 MB para não sobrecarregar a RAM
        block_size = 10 * 1024 * 1024  # 10 MB
        blocks = size_mb // 10
        remainder = (size_mb % 10) * 1024 * 1024
        
        # Gerar e escrever blocos de dados aleatórios
        for i in range(blocks):
            f.write(os.urandom(block_size))
            # Mostrar progresso a cada 100 MB
            if i % 10 == 0:
                print(f"  {i * 10}/{size_mb} MB escritos...")
        
        # Escrever o restante (se não for múltiplo de 10 MB)
        if remainder > 0:
            f.write(os.urandom(remainder))
    
    print(f"Ficheiro {TEST_FILE} criado com sucesso!")

def monitor_cpu(proc, stop_event, results_list):
    """Monitor CPU em background durante as operações"""
    # Monitorizar continuamente até receber sinal de paragem
    while not stop_event.is_set():
        cpu = proc.cpu_percent(interval=0.1)
        if cpu > 0:  # Só adicionar valores válidos
            results_list.append(cpu)

def run_bench(test_file: str = None):
    # Configuração dos parâmetros de teste
    sizes = [128, 192, 256]  # tamanhos de chave em bits
    modes = ["GCM", "CBC", "CTR", "CHACHA20", "3DES"]
    
    # Verificar se existe ficheiro de teste, caso contrário criar um
    if test_file is None or not os.path.exists(test_file):
        if not os.path.exists(TEST_FILE):
            make_test_file(10)  # cria ficheiro de 10MB
        test_file = TEST_FILE
    
    # Obter o tamanho do ficheiro original (plaintext)
    plain_len = os.path.getsize(test_file)
    
    # Preparar estrutura de diretórios para guardar ficheiros cifrados e decifrados
    output_dir = 'output'
    enc_dir = os.path.join(output_dir, 'encrypted')
    dec_dir = os.path.join(output_dir, 'decrypted')
    os.makedirs(enc_dir, exist_ok=True)
    os.makedirs(dec_dir, exist_ok=True)
    
    # Inicializar processo para medir recursos de CPU e memória
    proc = psutil.Process()
    
    results = []

    # Loop principal: testar cada combinação de tamanho de chave e modo criptográfico
    for bits in sizes:
        key = gen_key(bits) # Gerar chave criptográfica

        for mode in modes:
            print(f"Testando {mode} / {bits}-bit (3 repetições)...")
            
            # Listas para guardar resultados das 3 execuções (para calcular médias)
            cpu_samples_all = []
            enc_times = []
            dec_times = []
            mem_deltas = []
            
            # Repetir cada teste 3 vezes 
            for rep in range(3):
                print(f"  Repetição {rep+1}/3...")
                
                # Limpar memória antes de medir
                gc.collect()
                
                # Reset de contadores de CPU e memória
                proc.cpu_percent(interval=None)
                mem_before = proc.memory_info().rss
                
                # Iniciar monitor de CPU em background
                stop_event = threading.Event()
                cpu_samples = []
                cpu_thread = threading.Thread(target=monitor_cpu, args=(proc, stop_event, cpu_samples))
                cpu_thread.start()

                # Cifragem
                out_file = os.path.join(enc_dir, f'enc_{mode}_{bits}.bin')
                t0 = time.perf_counter()
                enc_res = encrypt_file(test_file, out_file, key, mode=mode)
                t1 = time.perf_counter()

                # Decifragem
                dec_out = os.path.join(dec_dir, f'dec_{mode}_{bits}.bin')
                dec_res = decrypt_file(out_file, dec_out, key)
                t2 = time.perf_counter()
                
                # Parar monitor de CPU
                stop_event.set()
                cpu_thread.join()
                
                # Guardar resultados desta repetição
                cpu_samples_all.extend(cpu_samples)
                enc_times.append(t1 - t0)
                dec_times.append(t2 - t1)
                mem_deltas.append(abs(proc.memory_info().rss - mem_before))
                
                # Pequeno delay entre repetições
                time.sleep(2)
            
            # Calcular médias das 3 execuções
            cpu_pct = sum(cpu_samples_all) / len(cpu_samples_all) if cpu_samples_all else 0
            enc_time = sum(enc_times) / len(enc_times)
            dec_time = sum(dec_times) / len(dec_times)
            mem_delta = sum(mem_deltas) / len(mem_deltas)

            # Métricas (usar valores da última execução para tamanhos)
            cipher_len = enc_res['ciphertext_len']
            total_time = enc_time + dec_time
            overhead_bytes = cipher_len - plain_len
            overhead_pct = (overhead_bytes / plain_len) * 100
            throughput = (plain_len / (1024 * 1024)) / enc_time if enc_time > 0 else 0
            time_per_kb = enc_time / (plain_len / 1024) if plain_len > 0 else 0

            # Guardar resultados finais
            results.append({
                'mode': mode,
                'bits': bits,
                'enc_time_s': enc_time,
                'dec_time_s': dec_time,
                'total_time_s': total_time,
                'cipher_len': cipher_len,
                'plain_len': plain_len,
                'overhead_bytes': overhead_bytes,
                'overhead_pct': overhead_pct,
                'throughput_mb_s': throughput,
                'time_per_kb': time_per_kb,
                'cpu_pct': cpu_pct,
                'mem_delta_bytes': mem_delta
            })


    # Exportar CSV (uma vez no fim)
    fieldnames = [
        'mode', 'bits',
        'enc_time_s', 'dec_time_s', 'total_time_s',
        'cipher_len', 'plain_len',
        'overhead_bytes', 'overhead_pct',
        'throughput_mb_s', 'time_per_kb',
        'cpu_pct', 'mem_delta_bytes'
    ]

    with open('benchmark_results.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    print("Benchmark concluído. Resultados em benchmark_results.csv")

if __name__ == "__main__":
    run_bench()

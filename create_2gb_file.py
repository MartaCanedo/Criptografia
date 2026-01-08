import os

filename = 'test_large_2gb.bin'
size_mb = 2000  # 2 GB

print(f"Criando {filename} com {size_mb} MB (2 GB)...")
print("Isso vai demorar alguns minutos...")

with open(filename, 'wb') as f:
    block_size = 10 * 1024 * 1024  # 10 MB por vez
    blocks = size_mb // 10
    
    for i in range(blocks):
        f.write(os.urandom(block_size))
        if i % 50 == 0:  # Mostrar progresso a cada 500 MB
            progress = (i * 10 / size_mb) * 100
            print(f"  Progresso: {i * 10} MB / {size_mb} MB ({progress:.1f}%)")

# Verificar tamanho final
final_size = os.path.getsize(filename)
final_size_mb = final_size / (1024 * 1024)
final_size_gb = final_size_mb / 1024

print(f"\n✓ Ficheiro criado com sucesso!")
print(f"  Nome: {filename}")
print(f"  Tamanho: {final_size_mb:.2f} MB ({final_size_gb:.2f} GB)")
print(f"  Localização atual")

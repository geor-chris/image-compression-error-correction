import hashlib
import base64
import json
import random
import requests

#Κάνουμε import τις συναρτήσεις
from arithmetic_coding import arithmetic_encode, decimal_to_binary_string
from linear_coding import generate_linear_code, encode_linear_block

def introduce_errors(binary_string, error_percentage):
    #Εισάγει τυχαία σφάλματα στο X% των bits
    bits = list(binary_string)
    total_bits = len(bits)
    
    #Υπολογίζουμε πόσα bits πρέπει να χαλάσουμε
    num_errors = int(total_bits * (error_percentage / 100.0))
    
    #Επιλέγουμε τυχαίες θέσεις (indices) για να κάνουμε τα σφάλματα
    error_indices = random.sample(range(total_bits), num_errors)
    
    for idx in error_indices:
         #aναστρέφουμε το bit (αν είναι 0 γίνεται 1, αν είναι 1 γίνεται 0)
        bits[idx] = '1' if bits[idx] == '0' else '0'
        
    return "".join(bits), num_errors

def main():
    #Διάβασμα Εικόνας
    image_path = ""
    
    while True:
        image_path = input("Δώσε το όνομα της εικόνας (π.χ. test.png): ").strip()
        
        if not image_path:
            print("[!] Παρακαλώ δώσε ένα έγκυρο όνομα αρχείου.")
            continue 
        try:
            print(f"[1] Διαβάζουμε την εικόνα: {image_path}...")
            with open(image_path, "rb") as f:
                image_data = f.read()
            break 
        except FileNotFoundError:
            print(f"[Σφάλμα] Το αρχείο '{image_path}' δεν βρέθηκε στον φάκελο! Δοκίμασε ξανά.\n")
    #Υπολογισμός SHA256
    #Το υπολογίζουμε στα αρχικά δεδομένα της εικόνας
    sha256_hash = hashlib.sha256(image_data).hexdigest()
    print(f"[2] Το SHA256 υπολογίστηκε: {sha256_hash[:10]}...")

    #Συμπίεση
    print("[3] Συμπίεση εικόνας...")
    
     #Κωδικοποίηση
    binary_string, probabilities, data_length = arithmetic_encode(image_data)    
    print("[4] Δημιουργία Γραμμικού Κώδικα και κωδικοποίηση...")
    k = 4
    n = 7
    P_matrix, G_matrix = generate_linear_code(k, n)
    encoded_bits, pad_len = encode_linear_block(binary_string, G_matrix, k)

    #Εισαγωγή Σφαλμάτων
    error_percent = float(input("Δώσε το ποσοστό σφάλματος (X%): "))
    noisy_bits, actual_errors = introduce_errors(encoded_bits, error_percent)
    print(f"[5] Προστέθηκαν {actual_errors} σφάλματα ({error_percent}%).")

    #Μετατροπή σε Base64 ---
    base64_encoded = base64.b64encode(noisy_bits.encode('ascii')).decode('ascii')

    #Πακετάρισμα σε JSON
    payload = {
        "encoded_image": base64_encoded,
        "compression_algorithm": "arithmetic",
        "encoding": "linear",
        "parameters": {
            "probabilities": {str(k): str(v) for k, v in probabilities.items()}, #Τα κάνουμε string για το JSON
            "data_length": data_length,
            "P_matrix": P_matrix,
            "k": k,
            "n": n,
            "pad_len": pad_len
        },
        "errors": actual_errors,
        "SHA256": sha256_hash,
        "entropy": 0 #Ο Server θα το υπολογίσει
    }

    #Αποστολή στον Server
    server_url = "http://127.0.0.1:5000/upload"
    print("[6] Αποστολή δεδομένων στον Server...")
    
    try:
        response = requests.post(server_url, json=payload)
        print("\n--- Απάντηση Server ---")
        print(response.json())
    except requests.exceptions.ConnectionError:
        print("\n[Σφάλμα] Ο Server δεν απαντάει. Σιγουρέψου ότι τρέχει (Βήμα 4)!")

if __name__ == "__main__":
    main()
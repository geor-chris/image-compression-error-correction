from flask import Flask, request, jsonify
import base64
import hashlib
import math
from collections import Counter
import io
from PIL import Image

#Εισαγωγή των συναρτήσεων
from arithmetic_coding import binary_string_to_decimal, arithmetic_decode
from linear_coding import decode_linear_block

app = Flask(__name__)

def calculate_entropy(data_bytes):
    #Υπολογίζει την Εντροπία  του αποκωδικοποιημένου μηνύματος."""
    if not data_bytes:
        return 0
    
    entropy = 0
    length = len(data_bytes)
    counts = Counter(data_bytes)
    
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
        
    return entropy

@app.route('/upload', methods=['POST'])
def handle_upload():
    try:
        from decimal import getcontext
        getcontext().prec = 5000
        
        #Λήψη του JSON
        data = request.json
        print("\n[+] Λήφθηκε νέο αίτημα από τον Client!")
        
        #Αποκωδικοποίηση Base64 σε bits
        base64_encoded = data['encoded_image']
        noisy_bits = base64.b64decode(base64_encoded).decode('ascii')
        
        #Ανάκτηση των παραμέτρων
        params = data['parameters']
        P_matrix = params['P_matrix']
        k = params['k']
        n = params['n']
        pad_len = params['pad_len']
        probabilities = params['probabilities']
        data_length = params['data_length']
        
        #Διόρθωση Σφαλμάτων 
        print("[*] Έναρξη διόρθωσης σφαλμάτων...")
        corrected_bits, errors_corrected = decode_linear_block(noisy_bits, P_matrix, k, n, pad_len)
        
        #Αποσυμπίεση
        print("[*] Έναρξη αποσυμπίεσης εικόνας...")
        decoded_decimal = binary_string_to_decimal(corrected_bits)
        decoded_bytes = arithmetic_decode(decoded_decimal, probabilities, data_length)
        
        #Έλεγχος αν είναι πραγματικά εικόνα (μέσω Pillow)
        is_valid_image = False
        try:
            # Το io.BytesIO μετατρέπει τα bytes σε "εικονικό αρχείο" στη μνήμη
            img = Image.open(io.BytesIO(decoded_bytes))
            img.verify() #Ελέγχει τα headers της εικόνας
            is_valid_image = True
            print("[+] Επιβεβαιώθηκε: Τα δεδομένα αποτελούν έγκυρη εικόνα.")
        except Exception:
            print("[-] Αποτυχία: Τα δεδομένα δεν αναγνωρίζονται ως εικόνα.")

        #Υπολογισμός Εντροπίας
        entropy_value = calculate_entropy(decoded_bytes)
        
        #Επαλήθευση SHA256
        server_sha256 = hashlib.sha256(decoded_bytes).hexdigest()
        sha256_match = (server_sha256 == data['SHA256'])
        
        #Υπολογισμός διαφοράς σφαλμάτων
        client_errors = data['errors']
        error_diff = client_errors - errors_corrected
        
        #Επιστροφή αποτελεσμάτων στον Client
        response = {
            "status": "success",
            "message": "Η αποκωδικοποίηση ολοκληρώθηκε",
            "is_valid_image": is_valid_image,
            "entropy": round(entropy_value, 4),
            "client_errors_injected": client_errors,
            "server_errors_corrected": errors_corrected,
            "error_difference": error_diff,
            "sha256_match": sha256_match
        }
        
        print(f"[+] Ολοκληρώθηκε! Διαφορά σφαλμάτων: {error_diff}. Εντροπία: {entropy_value:.4f}")
        return jsonify(response), 200

    except Exception as e:
        print(f"[!] Σφάλμα Server: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    #Ο Server ξεκινάει και ακούει στο port 5000
    app.run(host='127.0.0.1', port=5000, debug=True)
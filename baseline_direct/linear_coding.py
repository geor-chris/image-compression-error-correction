import numpy as np

def generate_linear_code(k=4, n=7):
    #Δημιουργεί έναν τυχαίο κώδικα. Επιστρέφει τον P, τον G και τον H
    #Φτιάχνουμε έναν τυχαίο πίνακα P με 0 και 1
    P = np.random.randint(2, size=(k, n - k))
    
    #Φτιάχνουμε τον Μοναδιαίο πίνακα I_k
    Ik = np.eye(k, dtype=int)
    
    #Συνενώνουμε οριζόντια τον I_k και τον P για να φτιάξουμε τον G
    G = np.hstack((Ik, P))
    
    return P.tolist(), G  #Επιστρέφουμε τον P ως list για να μπει εύκολα στο JSON

def encode_linear_block(binary_string, G, k):
    #Κωδικοποιεί το bitstring και προσθέτει padding αν χρειάζεται
    #Υπολογίζουμε πόσα μηδενικά λείπουν για να διαιρείται το μήκος ακριβώς με το k
    pad_len = (k - len(binary_string) % k) % k
    padded_bin = binary_string + '0' * pad_len
    
    encoded_bits = ""
    
    #Σπάμε το string σε blocks των k bits
    for i in range(0, len(padded_bin), k):
        block = padded_bin[i:i+k]
        
         #Μετατρέπουμε το block σε numpy array (διάνυσμα)
        u = np.array([int(bit) for bit in block])
        
        #Πολλαπλασιασμός: v = u * G mod 2
        v = np.dot(u, G) % 2
        
        #Το μετατρέπουμε ξανά σε string και το ενώνουμε
        encoded_bits += "".join(str(bit) for bit in v)
        
    return encoded_bits, pad_len


#Αποκωδικοποίηση/Διόρθωση
def decode_linear_block(received_bits, P_list, k, n, pad_len):
    #Αποκωδικοποιεί, διορθώνει 1-bit σφάλματα ανά block και αφαιρεί το padding
    #Ανακατασκευή του H από τη λίστα P του JSON
    P = np.array(P_list)
    Ink = np.eye(n - k, dtype=int)
    H = np.hstack((P.T, Ink))
    
   
    #υποθέτουμε ικανότητα διόρθωσης 1 σφάλματος ανά block
    syndrome_table = {}  #Φτιάχνουμε το Λεξικό (σύνδρομο)
    for i in range(n):
        e = np.zeros(n, dtype=int) #Διάνυσμα σφάλματος
        e[i] = 1                   #Βάζουμε 1 στη θέση του σφάλματος
        S = np.dot(e, H.T) % 2     #υπολογίζουμε το σύνδρομό του (S = e * H^T)
        
        S_tuple = tuple(S)
        if S_tuple not in syndrome_table: 
            syndrome_table[S_tuple] = e  #Αποθηκεύουμε ποιο διάνυσμα αντιστοιχεί σε αυτό το σύνδρομο
            
    #Προσθέτουμε την περίπτωση όπου το Σύνδρομο είναι 0 (κανένα σφάλμα)
    syndrome_table[tuple(np.zeros(n - k, dtype=int))] = np.zeros(n, dtype=int)

    decoded_bits = ""
    errors_corrected = 0
    
    #Αποκωδικοποίηση block-block
    for i in range(0, len(received_bits), n):
        block = received_bits[i:i+n]
        r = np.array([int(bit) for bit in block])
        
        #υπολογισμός Συνδρόμου: S = r * H^T mod 2
        S = np.dot(r, H.T) % 2
        S_tuple = tuple(S)
        
        #Αν υπάρχει σφάλμα και το σύνδρομο υπάρχει στο λεξικό μας
        if np.any(S != 0) and S_tuple in syndrome_table:
            e = syndrome_table[S_tuple]
            r = (r + e) % 2  #διάνυσμα σφάλματος
            errors_corrected += 1
            
        #έχει τα αρχικά δεδομένα στα πρώτα k bits
        u = r[:k]
        decoded_bits += "".join(str(bit) for bit in u)
        
    #Αφαίρεση του padding από το τέλος
    if pad_len > 0:
        decoded_bits = decoded_bits[:-pad_len]
        
    return decoded_bits, errors_corrected
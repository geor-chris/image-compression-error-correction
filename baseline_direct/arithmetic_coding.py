from decimal import Decimal, getcontext

#ορίζουμε τεράστια ακρίβεια για τα δεκαδικά ψηφία ώστε να μην χάσουμε δεδομένα
getcontext().prec = 5000
def get_probabilities(data): 
    #υπολογίζει την πιθανότητα εμφάνισης κάθε byte
    counts = {}
    for byte in data:
        if byte in counts:
            counts[byte] += 1
        else:
            counts[byte] = 1
            
    total_len = len(data)
    probabilities = {} #κενό λεξικό    

    for symbol, count in counts.items():
        #υπολογίζουμε την πιθανότητα ως Decimal για να μην χαθεί ακρίβεια
        prob = Decimal(count) / Decimal(total_len)
        
        #αποθηκεύουμε την πιθανότητα στο λεξικό με κλειδί το σύμβολο (byte)
        probabilities[symbol] = prob    
    
    return probabilities

def get_intervals(probabilities):
    #Χωρίζει το [0, 1) σε υποδιαστήματα βάσει των πιθανοτήτων
    intervals = {}
    low = Decimal(0)
    
    #ΤΑΞΙΝΟΜΗΣΗ
    for symbol in sorted(probabilities.keys()):
        prob = probabilities[symbol]
        high = low + prob
        
        intervals[symbol] = (low, high)
        low = high
        
    return intervals

def arithmetic_encode(data):
    
    #Παίρνει τα bytes της εικόνας και επιστρέφει: τον συμπιεσμένο δεκαδικό αριθμό και το λεξικό πιθανοτήτων 
    
    probabilities = get_probabilities(data)
    intervals = get_intervals(probabilities)

    low = Decimal(0)
    high = Decimal(1)

    for symbol in data:
        interval_range = high - low
        #στενεύουμε το διάστημα
        high = low + interval_range * intervals[symbol][1]
        low = low + interval_range * intervals[symbol][0]

    #οποιοσδήποτε αριθμός ανάμεσα στο low και το high είναι σωστός. 
   
    encoded_value = (low + high) / 2  #Παίρνουμε τον μέσο όρο
    
    return encoded_value, probabilities, len(data)

def arithmetic_decode(encoded_value, probabilities, data_length):
    """Ο Server χρησιμοποιεί αυτή τη συνάρτηση για να ανακτήσει την εικόνα."""
    #Ξαναφτιάχνουμε τα Decimals αν ήρθαν ως float από το JSON
    prob_decimals = {}

    for k, v in probabilities.items():
        byte_key = int(k)                 #μετατρέπουμε το κλειδί  ξανά σε ακέραιο 
        decimal_value = Decimal(str(v))   #φτιάχνουμε  το Decimal
        prob_decimals[byte_key] = decimal_value #το βάζουμε στο νέο λεξικό

    intervals = get_intervals(prob_decimals)
    
    decoded_data = bytearray()
    value = Decimal(str(encoded_value))

    for _ in range(data_length):
        for symbol, (low, high) in intervals.items():
            if low <= value < high:
                decoded_data.append(symbol)
                #αφαιρούμε το τρέχον όριο και κάνουμε scale up 
                interval_range = high - low
                value = (value - low) / interval_range
                break

    return bytes(decoded_data)


def decimal_to_binary_string(fraction, precision_bits=1000):
    #Μετατρέπει το δεκαδικό κλάσμα σε string από '0' και '1'
    binary_str = ""
    while fraction > 0 and len(binary_str) < precision_bits:
        fraction *= 2
        bit = int(fraction)
        if bit == 1:
            fraction -= 1
            binary_str += "1"
        else:
            binary_str += "0"
    return binary_str

def binary_string_to_decimal(binary_str):
    #αντίστροφη μετατροπή με αναγκαστική μέγιστη ακρίβεια στον Server
    from decimal import Decimal, getcontext
    
    #αναγκάζουμε τον Server να χρησιμοποιήσει τεράστια ακρίβεια
    getcontext().prec = 5000
    
    fraction = Decimal(0)
    for bit in reversed(binary_str):
        fraction = (fraction + Decimal(int(bit))) / Decimal(2)
        
    return fraction
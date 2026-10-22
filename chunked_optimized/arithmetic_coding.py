from decimal import Decimal, getcontext


getcontext().prec = 2000 

CHUNK_SIZE = 20       #Πόσα bytes θα διαβάζει κάθε φορά
CHUNK_BITS = 800      #Πόσα bits θα παράγει το κάθε κομμάτι 

def get_probabilities(data): 
    counts = {}
    for byte in data:
        if byte in counts:
            counts[byte] += 1
        else:
            counts[byte] = 1
            
    total_len = len(data)
    probabilities = {}   

    for symbol, count in counts.items():
        prob = Decimal(count) / Decimal(total_len)
        probabilities[symbol] = prob    
    
    return probabilities

def get_intervals(probabilities):
    intervals = {}
    low = Decimal(0)
    
    for symbol in sorted(probabilities.keys()):
        prob = probabilities[symbol]
        high = low + prob
        intervals[symbol] = (low, high)
        low = high
        
    return intervals

def decimal_to_binary_string(fraction, precision_bits):
    #Μετατρέπει σε bits και προσθέτει μηδενικά για να έχει ΠΑΝΤΑ σταθερό μήκος (CHUNK_BITS)
    binary_str = ""
    while fraction > 0 and len(binary_str) < precision_bits:
        fraction *= 2
        bit = int(fraction)
        if bit == 1:
            fraction -= 1
            binary_str += "1"
        else:
            binary_str += "0"
    
    #Γεμίζουμε με μηδενικά το τέλος για να κοπεί σωστά στον Server
    return binary_str.ljust(precision_bits, '0')

def binary_string_to_decimal(binary_str):
    from decimal import getcontext
    getcontext().prec = 2000
    
    fraction = Decimal(0)
    for bit in reversed(binary_str):
        fraction = (fraction + Decimal(int(bit))) / Decimal(2)
        
    return fraction

def arithmetic_encode(data):
    #Σπάει τα δεδομένα σε chunks, τα συμπιέζει και επιστρέφει απευθείας τα Bits
    probabilities = get_probabilities(data)
    intervals = get_intervals(probabilities)

    full_binary_string = ""

    #Loop που διαβάζει 40-40 τα bytes
    for i in range(0, len(data), CHUNK_SIZE):
        chunk = data[i:i+CHUNK_SIZE]
        low = Decimal(0)
        high = Decimal(1)

        for symbol in chunk:
            interval_range = high - low
            high = low + interval_range * intervals[symbol][1]
            low = low + interval_range * intervals[symbol][0]

        chunk_decimal = (low + high) / 2
        
        #Μετατροπή αυτού του μικρού chunk σε bits 
        chunk_bin = decimal_to_binary_string(chunk_decimal, CHUNK_BITS)
        full_binary_string += chunk_bin

    return full_binary_string, probabilities, len(data)

def arithmetic_decode(binary_string, probabilities, data_length):
    #Σπάει το τεράστιο bitstring του Server σε chunks και τα αποσυμπιέζει.
    prob_decimals = {}
    for k, v in probabilities.items():
        prob_decimals[int(k)] = Decimal(str(v))

    intervals = get_intervals(prob_decimals)
    decoded_data = bytearray()

    bytes_decoded = 0

    #Loop που διαβάζει 400-400 τα bits
    for i in range(0, len(binary_string), CHUNK_BITS):
        if bytes_decoded >= data_length:
            break

        chunk_bin = binary_string[i:i+CHUNK_BITS]
        chunk_decimal = binary_string_to_decimal(chunk_bin)
        value = Decimal(str(chunk_decimal))

        #Το τελευταίο chunk ίσως έχει λιγότερα από 40 bytes, υπολογίζουμε πόσα περιμένουμε
        bytes_in_this_chunk = min(CHUNK_SIZE, data_length - bytes_decoded)

        for _ in range(bytes_in_this_chunk):
            for symbol, (low, high) in intervals.items():
                if low <= value < high:
                    decoded_data.append(symbol)
                    interval_range = high - low
                    value = (value - low) / interval_range
                    bytes_decoded += 1
                    break

    return bytes(decoded_data)
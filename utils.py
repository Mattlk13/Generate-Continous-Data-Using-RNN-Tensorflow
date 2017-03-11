import numpy as np

def get_vocab(data_location, lowering = False):
    data_ = ""
    with open(data_location, 'r') as f:
        data_ += f.read()
    if lowering:
        data_ = data_.lower()
    
    vocab = list(set(data_))
    return data_, vocab

def embed_to_vocab(data_, vocab):
    data = np.zeros((len(data_), len(vocab)))
    pointer = 0
    for c in data_:
        v = [0.0] * len(vocab)
        v[vocab.index(c)] = 1.0
        data[pointer, :] = v
        pointer += 1

    return data

def decode_embed(array, vocab):
    return vocab[array.index(1)]
import tensorflow as tf
import numpy as np
from model import *
from utils import *
import random
import time
import matplotlib.pyplot as plt
import matplotlib as mp

mp.rcParams['lines.linewidth'] = .5

# This program originally created by http://www.cs.utoronto.ca/~ilya/pubs/2011/LANG-RNN.pdf
# So I write a similar program, but different code, any pipelining follows that publication

# Global settings ###########################################################################################

# lower is better, but slower
tf.app.flags.DEFINE_float("learning_rate", 0.01, "Learning rate.")
tf.app.flags.DEFINE_float("learning_rate_decay_factor", 0.99, "Learning rate decays by this much.")
tf.app.flags.DEFINE_integer("seq_length", 100, "Size of batches each training.")
tf.app.flags.DEFINE_integer("batch_size", 64, "Batch size to use during training.")
tf.app.flags.DEFINE_integer("max_epoch", 1000, "Limit on the size of training data (0: no limit).")

# reduce this size if your CPU/GPU Memory Crash
# I not recommend used larger RNN size of each layer and if trained using CPU or low GPU performance ; GTX 500 below
# I not recommend used larger number of nets layer if trained using CPU or low GPU performance ; GTX 500 below
tf.app.flags.DEFINE_integer("size", 256, "Size of each model layer.")
tf.app.flags.DEFINE_integer("num_layers", 2, "Number of layers in the model.")


# hidden layer model support:
# 1- simple lstm
# 2- lstm
# 3- gru
# 4- simple classic rnn
# 5- classic rnn

# this model to improve long term dependencies

# more read about LSTM (Long-Short-Term-Memory):
# http://colah.github.io/posts/2015-08-Understanding-LSTMs/

# more read about LSTM and GRU(Gated-Recurrent-Unit):
# http://www.wildml.com/2015/10/recurrent-neural-network-tutorial-part-4-implementing-a-grulstm-rnn-with-python-and-theano/
tf.app.flags.DEFINE_string("model_type", "gru", "Model for hidden layer")

# [] [] [] [] [] .. size
# [] [] [] [] [] .. size
# [] [] [] [] [] .. size
# [] = RNN cell
# size of layer depends num_layers
# default is 3

# change to False if want to train, True to generate text
tf.app.flags.DEFINE_boolean("decode", True, "Set to True for interactive decoding.")

# number of epoch/iteration
# 0 for infinite. press Interrupt key to stop the training if you feel ur training model trained enough

# change to data directory
tf.app.flags.DEFINE_string("data_dir", "/home/husein/Downloads/RNN/", "Data directory")

# change to train directory
tf.app.flags.DEFINE_string("train_dir", "/home/husein/Downloads/RNN/", "Training directory.")

# change to train datasets file name
tf.app.flags.DEFINE_string("train_data", "ccode.txt", "Training data.")

# change to output file name for decode session
tf.app.flags.DEFINE_string("output_data", "output.txt", "Output data.")

# the sentence generated during decode session will started by this sentence/word
# the life will continue... (example)
# included a space after a word
tf.app.flags.DEFINE_string("main_tag", "Aku ", "Main tag for sentence generated.")

# if you have a very large dataset, change this to True
# default is using int32
tf.app.flags.DEFINE_boolean("use_fp64", False, "Train using fp64 instead fp32.")

# this variables to limit GPU resources
# if I have 4GB of VRAM, 0.6 * 4GB = 2.4GB will be used
memory_duringtraining = 0.8
memory_duringtesting = 0.1

FLAGS = tf.app.flags.FLAGS

# Global settings ###########################################################################################

def listtotext(tofile, lists):
    fo = open(tofile, "wb")
    count = 0
    while(count < len(lists)):
            fo.write(lists[count])
            fo.write("\n")
            count += 1
    fo.close()

def get_data_type():
    return tf.float64 if FLAGS.use_fp64 else tf.float32

data, vocab = get_vocab(FLAGS.data_dir + FLAGS.train_data, lowering = False)
embed_data = embed_to_vocab(data, vocab)

print "\nPreparing data in %s" % (FLAGS.data_dir)
print("\nCreating RNN consist %d layers of %d RNN cells." % (FLAGS.num_layers, FLAGS.size))

config = tf.ConfigProto()
config.gpu_options.allocator_type = 'BFC'
    
if FLAGS.decode:
    config.gpu_options.per_process_gpu_memory_fraction=memory_duringtesting
else:
    config.gpu_options.per_process_gpu_memory_fraction=memory_duringtraining
        
sess = tf.InteractiveSession(config=config)
model = ModelRNN(FLAGS.model_type, FLAGS.batch_size, len(vocab), FLAGS.learning_rate, FLAGS.size, FLAGS.num_layers, get_data_type(), sess)

sess.run(tf.global_variables_initializer())

saver = tf.train.Saver(tf.global_variables())


def train():
    try:
	    saver.restore(sess, FLAGS.train_dir + "model.ckpt")
    except:
        print "start from fresh variables"
        
    last_time = time.time()
    
    batch = np.zeros((FLAGS.batch_size, FLAGS.seq_length, len(vocab)))
    batch_y = np.zeros((FLAGS.batch_size, FLAGS.seq_length, len(vocab)))
    
    possible_batch_id = range(embed_data.shape[0] - FLAGS.seq_length - 1)
    
    max_epoch = FLAGS.max_epoch
    X = []
    Y = []
    logs= []

    z = 0    
    while True:
        batch_id = random.sample(possible_batch_id, FLAGS.batch_size)
        
        #batching character-by-character
        for j in xrange(FLAGS.seq_length):
            
            id1 = [k+j for k in batch_id]
            id2 = [k+j+1 for k in batch_id]
            
            batch[:, j, :] = embed_data[id1, :]
            batch_y[:, j, :] = embed_data[id2, :]
    
        loss = model.train_batch(batch, batch_y)
        Y.append(loss)
        X.append(z)
        
        if ((z+1) % 100) == 0:
            new_time = time.time()
            diff = new_time - last_time
            last_time = new_time

            log = "batch: " + str(z+1) + ", loss: " + str(loss) + ", speed: " + str((100.0/diff)) + " batches / s"
            logs.append(log)
            print log
            saver.save(sess, FLAGS.train_dir + "model.ckpt")
            
        if ((z+1) % 1000) == 0:
            plt.plot(X, Y)
            plt.title(FLAGS.model_type + ' loss')
            plt.ylabel("Loss")
            plt.xlabel("Epoch")
            plt.savefig('loss.pdf')
            decode(testing = True)
        
        if((z+1) == max_epoch):
            listtotext('log.txt', logs)
            print "done training for " + str(z+1) + " epoch"
            exit(0)
        z += 1
            
            
            
            
def decode(testing = False, num = 100):
    try:
	    saver.restore(sess, FLAGS.train_dir + "model.ckpt")
    except:
        print "no pretrained model found"
        exit(0)
    
    path_output = FLAGS.data_dir + FLAGS.output_data
    
    if not testing:
        while True:
            num = raw_input("insert length of sentence: ")
            try:
                num = int(num)
                break
            except:
                print "please insert INTEGER only"
    
    for i in xrange(len(FLAGS.main_tag)):
        probs = model.step(embed_to_vocab(FLAGS.main_tag[i], vocab) , i == 0)
    
    sentence = FLAGS.main_tag
    
    for i in xrange(num):
        element = np.random.choice(range(len(vocab)), p=probs)
        sentence += vocab[element]
        probs = model.step(embed_to_vocab(vocab[element], vocab) , False)
        
    with open(path_output, 'wb') as f:
        f.write(sentence)
        
    print sentence
        

def main():
    if FLAGS.decode:
        decode()
    else:
        train()
        
        
main()
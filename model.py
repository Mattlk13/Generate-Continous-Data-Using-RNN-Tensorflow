import tensorflow as tf
import numpy as np

class ModelRNN:
    def __init__(self, model,batch_size, seq_length, learning_rate, rnn_size, net_layer, datatype, session):
        
        self.model = model
        
        #you can read more about these models on main.py
        if model == 'simple lstm':
            hidden_cell = tf.nn.rnn_cell.BasicLSTMCell
        elif model == 'lstm':
            hidden_cell = tf.nn.rnn_cell.LSTMCell
        elif model == 'gru':
            hidden_cell = tf.nn.rnn_cell.GRUCell
        elif model == 'simple classic rnn':
            hidden_cell = tf.nn.rnn_cell.BasicRNNCell
        elif model == 'classic rnn':
            hidden_cell = tf.nn.rnn_cell.RNNCell
        else:
            raise Exception("model type not supported: " + model)
        
        if(model == 'simple lstm' or model == 'lstm'):
            rnn_cells = hidden_cell(rnn_size, state_is_tuple = False)
        else:
            rnn_cells = hidden_cell(rnn_size)
        
        # Last state of LSTM, used when running the network in TEST mode
        if(model == 'simple lstm' or model == 'lstm'):
            self.net_last_state = np.zeros((net_layer * 2 * rnn_size))
        else:
            self.net_last_state = np.zeros((net_layer * rnn_size))
        
        self.rnn_size = rnn_size
        self.net_layer = net_layer
        
        # acted global variables to save sub value
        with tf.variable_scope('rnnnetwork'):
            
            #initialise size of our nets
            #number of cells in a layer times with number of layer
            if(model == 'simple lstm' or model == 'lstm'):
                self.rnn_cells =  tf.nn.rnn_cell.MultiRNNCell([rnn_cells] * net_layer, state_is_tuple = False)
            else:
                self.rnn_cells =  tf.nn.rnn_cell.MultiRNNCell([rnn_cells] * net_layer, state_is_tuple = False)
        
            self.input_data = tf.placeholder(datatype, shape=(None, None, seq_length))
            
            if(model == 'simple lstm' or model == 'lstm'):
                self.init_value = tf.placeholder(datatype, shape=(None, net_layer * 2 * rnn_size))
            else:
                self.init_value = tf.placeholder(datatype, shape=(None, net_layer * rnn_size))
        
            self.outputs, self.last_state = tf.nn.dynamic_rnn(self.rnn_cells, self.input_data, initial_state=self.init_value, dtype=datatype)
        
            self.session = session
        
            # Linear activation (FC layer on top of the LSTM net)
            self.rnn_W = tf.Variable(tf.random_normal((rnn_size, seq_length), stddev=0.01))
            self.rnn_B = tf.Variable(tf.random_normal((seq_length,), stddev=0.01))
            
            outputs_reshaped = tf.reshape(self.outputs, [-1, rnn_size])

            self.logits = (tf.matmul(outputs_reshaped, self.rnn_W) + self.rnn_B)
        
            batch_time_shape = tf.shape(self.outputs)
            self.final_outputs = tf.reshape(tf.nn.softmax(self.logits), (batch_time_shape[0], batch_time_shape[1], seq_length))
        
            self.y_batch = tf.placeholder(datatype, (None, None, seq_length))
            y_batch_long = tf.reshape(self.y_batch, [-1, seq_length])
        
            self.cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(self.logits, y_batch_long))
            self.optimizer = tf.train.RMSPropOptimizer(learning_rate, 0.9).minimize(self.cost)
        
    def step(self, x, init_zero_state=True):
        ## Reset the initial state of the network.
        if init_zero_state:
            if(self.model == 'simple lstm' or self.model == 'lstm'):
                init_value = np.zeros((self.net_layer * 2 * self.rnn_size,))
            else:
                init_value = np.zeros((self.net_layer * self.rnn_size,))
        else:
            init_value = self.net_last_state

        probs, next_lstm_state = self.session.run([self.final_outputs, self.last_state], feed_dict={self.input_data:[x], self.init_value:[init_value]})

        self.net_last_state = next_lstm_state[0]

        return probs[0][0]
    
    def train_batch(self, xbatch, ybatch):
        if(self.model == 'simple lstm' or self.model == 'lstm'):
            init_value = np.zeros((xbatch.shape[0], self.net_layer * 2 * self.rnn_size))
        else:
            init_value = np.zeros((xbatch.shape[0], self.net_layer * self.rnn_size))

        cost, _ = self.session.run([self.cost, self.optimizer], feed_dict={self.input_data:xbatch, self.y_batch:ybatch, self.init_value:init_value})

        return cost
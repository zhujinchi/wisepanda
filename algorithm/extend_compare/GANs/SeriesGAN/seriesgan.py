
# Necessary Packages
import tensorflow as tf
tf.compat.v1.disable_eager_execution()
from tensorflow.keras.layers import Dense, Input, TimeDistributed
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.layers import MultiHeadAttention, LayerNormalization, Dropout
from metrics.discriminative_metrics import discriminative_score_metrics
import warnings
warnings.filterwarnings('ignore')
warnings.filterwarnings('ignore', category=UserWarning, module='tensorflow')
warnings.filterwarnings('ignore', category=DeprecationWarning, module='tensorflow')
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

import numpy as np
from utils import extract_time, rnn_cell, random_generator, batch_generator
import math



def seriesgan (ori_data, parameters, num_samples):
    
  """SeriesGAN function.
  
  Use original data as training set to generater synthetic data (time-series)
  
  Args:
    - ori_data: original time-series data
    - parameters: SeriesGAN network parameters
    
  Returns:
    - generated_data: generated time-series data
  """

  # Initialization on the Graph
  tf.compat.v1.reset_default_graph()

  # Basic Parameters
  no, seq_len, dim = np.asarray(ori_data).shape
    
  # Maximum sequence length and each sequence length
  ori_time, max_seq_len = extract_time(ori_data)
  
  def MinMaxScaler(data):
    """Min-Max Normalizer.
    
    Args:
      - data: raw data
      
    Returns:
      - norm_data: normalized data
      - min_val: minimum values (for renormalization)
      - max_val: maximum values (for renormalization)
    """    
    min_val = np.min(np.min(data, axis = 0), axis = 0)
    data = data - min_val
      
    max_val = np.max(np.max(data, axis = 0), axis = 0)
    norm_data = data / (max_val + 1e-7)
      
    return data, min_val, max_val
  
  # Normalization
  ori_data, min_val, max_val = MinMaxScaler(ori_data)
              
  ## Build a RNN networks   
  

  #---------------------------------
  
  # Network Parameters
  if parameters['hidden_dim'] == 'same':
     hidden_dim = dim
  else:  
     hidden_dim   = parameters['hidden_dim'] 
        
  num_layers   = parameters['num_layer']
  iterations   = parameters['iterations']
  batch_size   = parameters['batch_size']
  z_dim        = dim
  gamma        = 1
  beta         = 1
  temporal_dimension = 16
    
  # Input place holders
  X = tf.compat.v1.placeholder(tf.float32, [None, max_seq_len, dim], name = "myinput_x")
  Z = tf.compat.v1.placeholder(tf.float32, [None, max_seq_len, z_dim], name = "myinput_z")
  T = tf.compat.v1.placeholder(tf.int32, [None], name = "myinput_t")
    
  final_generated = []
  saver = None
  global_summing = 5
  #---------------------------------


  def temporal_embedder(X, T):
    with tf.compat.v1.variable_scope("temporal_embedder", reuse=tf.compat.v1.AUTO_REUSE):
        
        # GRU layers
        e_cell = tf.compat.v1.nn.rnn_cell.MultiRNNCell([tf.compat.v1.nn.rnn_cell.GRUCell(dim, activation=tf.nn.tanh) for _ in range(num_layers)])
        e_outputs, e_last_states = tf.compat.v1.nn.dynamic_rnn(e_cell, X, dtype=tf.float32, sequence_length=T)
        
        # Fully connected layer to reduce the timestamps dimension
        H = tf.compat.v1.layers.dense(e_last_states[-1], temporal_dimension, activation=None)     
        
    return H


  def temporal_recovery(H_t, T):
    with tf.compat.v1.variable_scope("temporal_recovery", reuse=tf.compat.v1.AUTO_REUSE):
        
        # Fully connected layer to expand the compressed representation
        expanded_H = tf.compat.v1.layers.dense(H_t, max_seq_len * dim, activation=None)
        
        # Reshape to match the expected input of GRU layers
        expanded_H = tf.reshape(expanded_H, [-1, max_seq_len, dim])
        
        # GRU layers
        r_cell = tf.compat.v1.nn.rnn_cell.MultiRNNCell([tf.compat.v1.nn.rnn_cell.GRUCell(dim, activation=tf.nn.tanh) for _ in range(num_layers)])
        r_outputs, r_last_states = tf.compat.v1.nn.dynamic_rnn(r_cell, expanded_H, dtype=tf.float32)
        
        # Fully connected layer to reconstruct the original feature dimensions
        X_tilde = tf.compat.v1.layers.dense(r_outputs, dim, activation=None)
        
    return X_tilde



  def embedder(X, T):
    with tf.compat.v1.variable_scope("embedder", reuse=tf.compat.v1.AUTO_REUSE):
        
        
        # GRU layers
        e_cell = tf.compat.v1.nn.rnn_cell.MultiRNNCell([tf.compat.v1.nn.rnn_cell.GRUCell(hidden_dim, activation=tf.nn.tanh) for _ in range(num_layers)])
        e_outputs, e_last_states = tf.compat.v1.nn.dynamic_rnn(e_cell, X, dtype=tf.float32, sequence_length=T)
        
        # Fully connected layer
        H = tf.compat.v1.layers.dense(e_outputs, hidden_dim, activation=None)     
        
    return H


  def recovery(H, T):
    with tf.compat.v1.variable_scope("recovery", reuse=tf.compat.v1.AUTO_REUSE):

        
        # GRU layers
        r_cell = tf.compat.v1.nn.rnn_cell.MultiRNNCell([tf.compat.v1.nn.rnn_cell.GRUCell(hidden_dim, activation=tf.nn.tanh) for _ in range(num_layers)])
        r_outputs, r_last_states = tf.compat.v1.nn.dynamic_rnn(r_cell, H, dtype=tf.float32, sequence_length=T)
        
        # Fully connected layer
        X_tilde = tf.compat.v1.layers.dense(r_outputs, hidden_dim, activation=None)
        
    return X_tilde


  def generator(Z, T):
    with tf.compat.v1.variable_scope("generator", reuse=tf.compat.v1.AUTO_REUSE):
        
        
        # GRU layers
        g_cell = tf.compat.v1.nn.rnn_cell.MultiRNNCell([tf.compat.v1.nn.rnn_cell.GRUCell(hidden_dim, activation=tf.nn.tanh) for _ in range(num_layers)])
        g_outputs, g_last_states = tf.compat.v1.nn.dynamic_rnn(g_cell, Z, dtype=tf.float32, sequence_length=T)
        
        # Fully connected layer
        E = tf.compat.v1.layers.dense(g_outputs, hidden_dim, activation=None)
        
    return E

  def supervisor(H, T):
    with tf.compat.v1.variable_scope("supervisor", reuse=tf.compat.v1.AUTO_REUSE):

        
        # GRU layers
        s_cell = tf.compat.v1.nn.rnn_cell.MultiRNNCell([tf.compat.v1.nn.rnn_cell.GRUCell(hidden_dim, activation=tf.nn.tanh) for _ in range(num_layers -1)])
        s_outputs, s_last_states = tf.compat.v1.nn.dynamic_rnn(s_cell, H, dtype=tf.float32, sequence_length=T)
        
        # Fully connected layer
        S = tf.compat.v1.layers.dense(s_outputs, hidden_dim, activation=None)
        
    return S

          

  def discriminator(H, T):
    with tf.compat.v1.variable_scope("discriminator", reuse=tf.compat.v1.AUTO_REUSE):

        
        # GRU layers
        d_cell = tf.compat.v1.nn.rnn_cell.MultiRNNCell([tf.compat.v1.nn.rnn_cell.GRUCell(hidden_dim, activation=tf.nn.tanh) for _ in range(num_layers)])
        d_outputs, d_last_states = tf.compat.v1.nn.dynamic_rnn(d_cell, H, dtype=tf.float32, sequence_length=T)
        
        # Flatten and dense layer
        flattened_input = tf.keras.layers.Flatten()(d_outputs)
        Y_hat = tf.compat.v1.layers.dense(d_outputs, hidden_dim, activation=None)
        
    return Y_hat

  def ae_discriminator(X, T):
    with tf.compat.v1.variable_scope("ae_discriminator", reuse=tf.compat.v1.AUTO_REUSE):
        
        # GRU layers
        d_cell = tf.compat.v1.nn.rnn_cell.MultiRNNCell([tf.compat.v1.nn.rnn_cell.GRUCell(hidden_dim, activation=tf.nn.tanh) for _ in range(num_layers)])
        d_outputs, d_last_states = tf.compat.v1.nn.dynamic_rnn(d_cell, X, dtype=tf.float32, sequence_length=T)
        
        # Flatten and dense layer
        flattened_input = tf.keras.layers.Flatten()(d_outputs)
        Y_hat_ae = tf.compat.v1.layers.dense(flattened_input, hidden_dim, activation=None)
        
    return Y_hat_ae



  #---------------------------------
    
  
    
  # Embedder & Recovery
  H = embedder(X, T)
  X_tilde = recovery(H, T)

  Y_ae_fake = ae_discriminator(X_tilde, T)
  Y_ae_real = ae_discriminator(X, T)     
    
  # Generator
  E_hat = generator(Z, T)
  H_hat = supervisor(E_hat, T)
  H_hat_supervise = supervisor(H, T)
    
  # Synthetic data
  X_hat = recovery(H_hat, T)
    
  Y_ae_fake_e = ae_discriminator(X_hat, T)
  X_tilde_fake_second = recovery(E_hat, T)
  Y_ae_fake_e_second = ae_discriminator(X_tilde_fake_second, T)
   
    
  # Discriminator
  Y_fake = discriminator(H_hat, T)
  Y_real = discriminator(H, T)     
  Y_fake_e = discriminator(E_hat, T)
    
  H_t = temporal_embedder(X, T)
  X_t = temporal_recovery(H_t, T)
  H_t_hat = temporal_embedder(X_hat, T)
    
  #---------------------------------

    
  # Variables
  e_t_vars = [v for v in tf.compat.v1.trainable_variables() if v.name.startswith('temporal_embedder')]
  r_t_vars = [v for v in tf.compat.v1.trainable_variables() if v.name.startswith('temporal_recovery')]
  e_vars = [v for v in tf.compat.v1.trainable_variables() if v.name.startswith('embedder')]
  r_vars = [v for v in tf.compat.v1.trainable_variables() if v.name.startswith('recovery')]
  d_ae_vars = [v for v in tf.compat.v1.trainable_variables() if v.name.startswith('ae_discriminator')]
  g_vars = [v for v in tf.compat.v1.trainable_variables() if v.name.startswith('generator')]
  s_vars = [v for v in tf.compat.v1.trainable_variables() if v.name.startswith('supervisor')]
  d_vars = [v for v in tf.compat.v1.trainable_variables() if v.name.startswith('discriminator')]

  #---------------------------------

    
  # Discriminator loss
  D_loss_real = tf.reduce_mean(tf.math.squared_difference(Y_real, tf.ones_like(Y_real)))
  D_loss_fake = tf.reduce_mean(tf.square(Y_fake))
  D_loss_fake_e = tf.reduce_mean(tf.square(Y_fake_e))
  D_loss = D_loss_real + D_loss_fake + gamma * D_loss_fake_e
  #D_loss_real = tf.compat.v1.losses.sigmoid_cross_entropy(tf.ones_like(Y_real), Y_real)
  #D_loss_fake = tf.compat.v1.losses.sigmoid_cross_entropy(tf.zeros_like(Y_fake), Y_fake)
  #D_loss_fake_e = tf.compat.v1.losses.sigmoid_cross_entropy(tf.zeros_like(Y_fake_e), Y_fake_e)
  #D_loss = D_loss_real + D_loss_fake + gamma * D_loss_fake_e

  # AE Discriminator loss
  D_ae_loss_real = tf.reduce_mean(tf.math.squared_difference(Y_ae_real, tf.ones_like(Y_ae_real)))
  D_ae_loss_fake = tf.reduce_mean(tf.square(Y_ae_fake))
  D_ae_loss_fake_e = tf.reduce_mean(tf.square(Y_ae_fake_e))
  D_ae_loss_fake_e_second = tf.reduce_mean(tf.square(Y_ae_fake_e_second))

  D_ae_loss = D_ae_loss_real + D_ae_loss_fake  
  D_ae_loss_real_second = tf.reduce_mean(tf.math.squared_difference(Y_ae_fake, tf.ones_like(Y_ae_fake)))
  D_ae_loss_second = D_ae_loss_real + D_ae_loss_real_second + beta * (D_ae_loss_fake_e + gamma * D_ae_loss_fake_e_second)
    
    
  # Generator loss
  # 1. Adversarial loss
  G_loss_U = tf.reduce_mean(tf.math.squared_difference(tf.ones_like(Y_fake), Y_fake))
  G_loss_U_e = tf.reduce_mean(tf.math.squared_difference(tf.ones_like(Y_fake_e), Y_fake_e))
  #G_loss_U = tf.compat.v1.losses.sigmoid_cross_entropy(tf.ones_like(Y_fake), Y_fake)
  #G_loss_U_e = tf.compat.v1.losses.sigmoid_cross_entropy(tf.ones_like(Y_fake_e), Y_fake_e)
    
  G_loss_U_ae = tf.reduce_mean(tf.math.squared_difference(tf.ones_like(Y_ae_fake_e), Y_ae_fake_e))
  G_loss_U_ae_e = tf.reduce_mean(tf.math.squared_difference(tf.ones_like(Y_ae_fake_e_second), Y_ae_fake_e_second)) 
    
  G_loss_U_totall = G_loss_U + G_loss_U_e + G_loss_U_ae + G_loss_U_ae_e
    
  # 2. Supervised loss
  G_loss_S = tf.reduce_mean(tf.math.squared_difference(H[:,2:,:], H_hat_supervise[:,:-2,:]))


  #---------
  # 3. Time Series Characteristics
    
  mean_H_t = tf.reduce_mean(H_t, axis=0)
  mean_H_t_hat = tf.reduce_mean(H_t_hat, axis=0)

  # Compute the MSE between the means
  mse_mean = tf.reduce_mean(tf.square(mean_H_t - mean_H_t_hat))

  # Compute the standard deviation along the 0 axis
  std_H_t = tf.math.reduce_std(H_t, axis=0)
  std_H_t_hat = tf.math.reduce_std(H_t_hat, axis=0)

  # Compute the MSE between the standard deviations
  mse_std = tf.reduce_mean(tf.square(std_H_t - std_H_t_hat))

  G_loss_ts = mse_mean + mse_std
    
  #---------

  # 4. Two Momments
  G_loss_V1 = tf.reduce_mean(tf.abs(tf.sqrt(tf.nn.moments(X_hat,[0])[1] + 1e-6) - tf.sqrt(tf.nn.moments(X,[0])[1] + 1e-6)))
  G_loss_V2 = tf.reduce_mean(tf.abs((tf.nn.moments(X_hat,[0])[0]) - (tf.nn.moments(X,[0])[0])))
    
  G_loss_V = G_loss_V1 + G_loss_V2
        
  # 5. Summation
  G_loss =  G_loss_U + gamma * G_loss_U_e + beta * (G_loss_U_ae + gamma * G_loss_U_ae_e) + 20 * tf.sqrt(G_loss_S) + 10 * G_loss_V + 20 * G_loss_ts
    
    
  # Embedder network loss
  lambda_c = 0.001
  E_loss_T00 = tf.compat.v1.losses.mean_squared_error(X, X_tilde)
  E_loss_U = tf.reduce_mean(tf.math.squared_difference(tf.ones_like(Y_ae_fake), Y_ae_fake))
  E_loss_U_e = tf.reduce_mean(tf.math.squared_difference(tf.ones_like(Y_ae_fake_e), Y_ae_fake_e))
  E_loss_U_e_second = tf.reduce_mean(tf.math.squared_difference(tf.ones_like(Y_ae_fake_e_second), Y_ae_fake_e_second))
        
  E_loss_T0 = E_loss_T00 + lambda_c*E_loss_U
  E_loss_T0_second = E_loss_T00 + 0.1 * ( lambda_c*E_loss_U + lambda_c* beta * 0.1 *(E_loss_U_e + gamma * E_loss_U_e_second))
  E_loss0 = tf.sqrt(E_loss_T0)
  E_loss = tf.sqrt(E_loss_T0_second) + 0.01 * G_loss_S
    
    
    
  E_loss_temporal = tf.compat.v1.losses.mean_squared_error(X, X_t)
  #---------------------------------


  # optimizer
  E_solver_temporal = tf.compat.v1.train.AdamOptimizer().minimize(E_loss_temporal, var_list = e_t_vars + r_t_vars)
  E0_solver = tf.compat.v1.train.AdamOptimizer().minimize(E_loss0, var_list = e_vars + r_vars)
  E_solver = tf.compat.v1.train.AdamOptimizer().minimize(E_loss, var_list = e_vars + r_vars)
  D_ae_solver = tf.compat.v1.train.AdamOptimizer().minimize(D_ae_loss, var_list = d_ae_vars)
  D_ae_solver_second = tf.compat.v1.train.AdamOptimizer().minimize(D_ae_loss_second, var_list = d_ae_vars)
  D_solver = tf.compat.v1.train.AdamOptimizer().minimize(D_loss, var_list = d_vars)
  G_solver = tf.compat.v1.train.AdamOptimizer().minimize(G_loss, var_list = g_vars + s_vars)      
  GS_solver = tf.compat.v1.train.AdamOptimizer().minimize(G_loss_S, var_list = g_vars + s_vars)   

  #---------------------------------

        
  ## SeriesGAN training   
  sess = tf.compat.v1.Session()
  sess.run(tf.compat.v1.global_variables_initializer())

  # 1. Autoencoder Training for Loss
  print('Start Autoencoder Training for Loss')
    
  for itt in range(int(iterations*0.5)):
    for kk in range(2):
        # Set mini-batch
        X_mb, T_mb = batch_generator(ori_data, ori_time, batch_size)           
        # Train embedder        
        _, step_e_loss = sess.run([E_solver_temporal, E_loss_temporal], feed_dict={X: X_mb, T: T_mb})        
        # Checkpoint

    if itt % 500 == 0 or itt==int(iterations*0.5)-1:
      print('step: '+ str(itt*2) + '/' + str(iterations) + ', AE_loss: ' + str(np.round(step_e_loss,4))) 
      
  print('Finish Autoencoder Training for Loss')
    
    
  # 2. Embedding network training
  print('Start Embedding Network Training')
    
  for itt in range(int(iterations*0.5)):
    for kk in range(2):
      # Set mini-batch
      X_mb, T_mb = batch_generator(ori_data, ori_time, batch_size)           
      # Train embedder        
      _, step_e_loss = sess.run([E0_solver, E_loss0], feed_dict={X: X_mb, T: T_mb})        
      # Checkpoint
    
    check_d_ae_loss = sess.run(D_ae_loss, feed_dict={X: X_mb, T: T_mb})
    # Train discriminator (only when the discriminator does not work well)
    if (check_d_ae_loss > 0.15):        
      _, step_d_ae_loss = sess.run([D_ae_solver, D_ae_loss], feed_dict={X: X_mb, T: T_mb})
    
    if itt % 500 == 0 or itt==int(iterations*0.5)-1:
      print('step: '+ str(itt*2) + '/' + str(iterations) + ', AE_loss: ' + str(np.round(step_e_loss,4)) 
           + ', AE_D_loss: ' + str(np.round(step_d_ae_loss,4))) 
      
  print('Finish Embedding Network Training')
    
  # 3. Training only with supervised loss
  print('Start Training with Supervised Loss Only')
    
  for itt in range(iterations):
    # Set mini-batch
    X_mb, T_mb = batch_generator(ori_data, ori_time, batch_size)    
    # Random vector generation   
    Z_mb = random_generator(batch_size, z_dim, T_mb, max_seq_len)
    # Train generator       
    _, step_g_loss_s = sess.run([GS_solver, G_loss_S], feed_dict={Z: Z_mb, X: X_mb, T: T_mb})       
    # Checkpoint
    if itt % 1000 == 0 or itt==iterations-1:
      print('step: '+ str(itt)  + '/' + str(iterations) +', S_loss: ' + str(np.round(step_g_loss_s,4)) )
      
  print('Finish Training with Supervised Loss Only')


  print('Start Joint Training')
  
  for itt in range(iterations):
    # Generator training (twice more than discriminator training)
    for kk in range(2):
      # Set mini-batch
      X_mb, T_mb = batch_generator(ori_data, ori_time, batch_size)               
      # Random vector generation
      Z_mb = random_generator(batch_size, z_dim, T_mb, max_seq_len)
      # Train generator
      _, step_g_loss_u, step_g_loss_s, step_g_loss, step_g_loss_ts_structure = sess.run([G_solver, G_loss_U_totall, G_loss_S, G_loss, G_loss_ts], feed_dict={Z: Z_mb, X: X_mb, T: T_mb})
       # Train embedder        
      _, step_e_loss_t0 = sess.run([E_solver, E_loss], feed_dict={Z: Z_mb, X: X_mb, T: T_mb})   
           
    # Discriminator training        
    # Set mini-batch
    X_mb, T_mb = batch_generator(ori_data, ori_time, batch_size)           
    # Random vector generation
    Z_mb = random_generator(batch_size, z_dim, T_mb, max_seq_len)
    # Check discriminator loss before updating
    check_d_loss = sess.run(D_loss, feed_dict={X: X_mb, T: T_mb, Z: Z_mb})
    # Train discriminator (only when the discriminator does not work well)
    if (check_d_loss > 0.15):        
      _, step_d_loss = sess.run([D_solver, D_loss], feed_dict={X: X_mb, T: T_mb, Z: Z_mb})
    
    check_d_ae_loss = sess.run(D_ae_loss_second, feed_dict={X: X_mb, T: T_mb, Z: Z_mb})
    # Train discriminator (only when the discriminator does not work well)
    if (check_d_ae_loss > 0.15):        
      _, step_d_ae_loss = sess.run([D_ae_solver_second, D_ae_loss_second], feed_dict={X: X_mb, T: T_mb, Z: Z_mb})
        
    # Print multiple checkpoints
    if itt % 1000 == 0 or itt==iterations-1:
      print('step: '+ str(itt) + '/' + str(iterations) + 
            ', D_loss: ' + str(np.round(step_d_loss,4)) + 
            ', G_loss: ' + str(np.round(step_g_loss,4)) + 
            ', G_loss_u: ' + str(np.round(step_g_loss_u,4)) + 
            ', G_loss_s: ' + str(np.round(step_g_loss_s,4)) + 
            ', G_loss_ts: ' + str(np.round(step_g_loss_ts_structure,4)) + 
            ', AE_loss: ' + str(np.round(step_e_loss_t0,4)) +
            ', AE_D_loss: ' + str(np.round(step_d_ae_loss,4))
           )  
    
    if (itt >= int(iterations*0.5)) and (itt % 500 == 0 or itt==iterations-1):
        
        saver = tf.compat.v1.train.Saver()
        Z_mb = random_generator(no, z_dim, ori_time, max_seq_len)
        generated_data_curr = sess.run(X_hat, feed_dict={Z: Z_mb, X: ori_data, T: ori_time})    
        generated_data = list()
        for i in range(no):
            temp = generated_data_curr[i,:ori_time[i],:]
            generated_data.append(temp)
        # Renormalization
        generated_data = generated_data * max_val
        generated_data = generated_data + min_val
        
        
        metric_iteration = 6
        discriminative_score = list()
        for _ in range(metric_iteration):
            temp_disc = discriminative_score_metrics(ori_data, generated_data)
            discriminative_score.append(temp_disc)
            
        discriminative_score = np.array(discriminative_score)
        
        mean_dis_score = np.round(np.min(discriminative_score), 4)
        
        summing = mean_dis_score
            
        if summing <= global_summing:
            global_summing = summing
            final_generated = generated_data
        
  print('Finish Joint Training')

  #-------------------------------------------------------------------
    
  if num_samples == "same":
   
    return final_generated

  else:
    count = int(num_samples / no)
  
    all_generated_data = []
    for c in range(count):
        Z_mb = random_generator(no, z_dim, ori_time, max_seq_len)
        generated_data_curr = sess.run(X_hat, feed_dict={Z: Z_mb, X: ori_data, T: ori_time})    
        generated_data = []
        for i in range(no):
          temp = generated_data_curr[i,:ori_time[i],:]
          generated_data.append(temp)

        # Renormalization
        generated_data = generated_data * max_val
        generated_data = generated_data + min_val

        all_generated_data.append(generated_data)
    all_generated_data = np.concatenate(all_generated_data)

    return all_generated_data
                
  #-------------------------------------------------------------------
  
    
  

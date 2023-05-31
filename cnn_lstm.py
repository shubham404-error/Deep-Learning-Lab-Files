# -*- coding: utf-8 -*-
"""CNN-LSTM.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1d6s2s-nGOmfqfzGxHiZLWJX5A9uV5ZW9
"""

import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
from scipy import stats
import tensorflow as tf
import seaborn as sns
from pylab import rcParams
from sklearn import metrics
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, auc, roc_curve, roc_auc_score, precision_score, recall_score, f1_score, accuracy_score, classification_report, SCORERS, log_loss
######################################################################################################################
sns.set(style='whitegrid', palette='muted', font_scale=1.5)
rcParams['figure.figsize'] = 10, 6
############################################### load data #############################################################
RANDOM_SEED = 42
columns = ['user','activity','timestamp', 'x-axis', 'y-axis', 'z-axis']
df = pd.read_csv('data/WISDM_ar_v1.1_raw.txt', header = None, names = columns)
df = df.dropna()
df.head()
df.info()
####################################################################################################
N_TIME_STEPS = 90
N_FEATURES = 3
step = 20
segments = []
labels = []
for i in range(0, len(df) - N_TIME_STEPS, step):
    xs = df['x-axis'].values[i: i + N_TIME_STEPS]
    ys = df['y-axis'].values[i: i + N_TIME_STEPS]
    zs = df['z-axis'].values[i: i + N_TIME_STEPS]
    label = stats.mode(df['activity'][i: i + N_TIME_STEPS])[0][0]
    segments.append([xs, ys, zs])
    labels.append(label)
reshaped_segments = np.asarray(segments, dtype= np.float32).reshape(-1, N_TIME_STEPS, N_FEATURES)
labels = np.asarray(pd.get_dummies(labels), dtype = np.float32)
X_train, X_test, y_train, y_test = train_test_split(
        reshaped_segments, labels, test_size=0.2, random_state=RANDOM_SEED)
#########################################################################################################################
N_CLASSES = 6
N_HIDDEN_UNITS = 32
keep_prob_ = 0.5
lstm_layers=2
def create_CNNLSTM_model(input):
	conv1 = tf.layers.conv1d(inputs=input, filters=32, kernel_size=5, strides=1, padding='same', activation = tf.nn.relu)
	conv2 = tf.layers.conv1d(inputs=conv1, filters=32, kernel_size=5, strides=1, padding='same', activation = tf.nn.relu)
	#conv3 = tf.layers.conv1d(inputs=conv2, filters=32, kernel_size=5, strides=1, padding='same', activation = tf.nn.relu)
	n_ch = 32
	lstm_in = tf.transpose(conv2, [1,0,2]) # reshape into (seq_len, batch, channels)
	lstm_in = tf.reshape(lstm_in, [-1, n_ch]) # Now (seq_len*batch, n_channels)
	# To cells
	lstm_in = tf.layers.dense(lstm_in, N_HIDDEN_UNITS, activation=None) # or tf.nn.relu, tf.nn.sigmoid, tf.nn.tanh?
    
	# Open up the tensor into a list of seq_len pieces
	lstm_in = tf.split(lstm_in, N_TIME_STEPS, 0)
    
	# Add LSTM layers
	lstm = [tf.contrib.rnn.BasicLSTMCell(N_HIDDEN_UNITS, forget_bias=1.0) for _ in range(2)]
	cell = tf.contrib.rnn.MultiRNNCell(lstm)
	outputs, final_state = tf.contrib.rnn.static_rnn(cell, lstm_in, dtype=tf.float32)
    
	# We only need the last output tensor to pass into a classifier
	logits = tf.layers.dense(outputs[-1], N_CLASSES)
	return logits
	
tf.reset_default_graph()

X = tf.placeholder(tf.float32, [None, N_TIME_STEPS, N_FEATURES], name="input")
Y = tf.placeholder(tf.float32, [None, N_CLASSES])
######################################################################################################################
pred_Y = create_CNNLSTM_model(X)
pred_softmax = tf.nn.softmax(pred_Y, name="y_")
L2_LOSS = 0.0015
l2 = L2_LOSS * \
    sum(tf.nn.l2_loss(tf_var) for tf_var in tf.trainable_variables())
loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits = pred_Y, labels = Y)) + l2
LEARNING_RATE = 0.0025
optimizer = tf.train.AdamOptimizer(learning_rate=LEARNING_RATE).minimize(loss)
correct_pred = tf.equal(tf.argmax(pred_softmax, 1), tf.argmax(Y, 1))
accuracy = tf.reduce_mean(tf.cast(correct_pred, dtype=tf.float32))
########################################################################################################################
	
N_EPOCHS = 50 #50
BATCH_SIZE = 64
########################################################################################################################
saver = tf.train.Saver()
history = dict(train_loss=[], 
                     train_acc=[], 
                     test_loss=[], 
                     test_acc=[])
sess=tf.InteractiveSession()
sess.run(tf.global_variables_initializer())
#saver.restore(sess, "./checkpoint/har.ckpt")
train_count = len(X_train)
for i in range(1, N_EPOCHS + 1):
    for start, end in zip(range(0, train_count, BATCH_SIZE),
                          range(BATCH_SIZE, train_count + 1,BATCH_SIZE)):
        sess.run(optimizer, feed_dict={X: X_train[start:end],
                                       Y: y_train[start:end]})
    _, acc_train, loss_train = sess.run([pred_softmax, accuracy, loss], feed_dict={
                                            X: X_train, Y: y_train})

    _, acc_test, loss_test = sess.run([pred_softmax, accuracy, loss], feed_dict={
                                            X: X_test, Y: y_test})
    history['train_loss'].append(loss_train)
    history['train_acc'].append(acc_train)
    history['test_loss'].append(loss_test)
    history['test_acc'].append(acc_test)
######################################################################################################################
    print(f'epoch: {i} train accuracy: {acc_train} train loss: {loss_train} test accuracy: {acc_test} test loss: {loss_test}')
########################################################################################################## #########3#
    plt.figure(figsize=(10, 6))
    plt.plot(np.array(history['train_acc']), "orange", label="Training accuracy")
    plt.plot(np.array(history['test_acc']), "blue",   label="Testing accuracy")
    plt.title('Accuracy for CNN-LSTM')
    plt.legend(loc='lower right')
    plt.ylabel('Accuracy')
    plt.xlabel('Epochs')
    plt.xlim()
    plt.ylim(0.8)
    #plt.savefig('figure1')
    plt.show()
#####################################################################################################################
    plt.figure(figsize=(10, 6))
    plt.plot(np.array(history['train_loss']), "orange", label="Training loss")
    plt.plot(np.array(history['test_loss']), "blue",   label="Testing loss")
    plt.title('Loss for CNN-LSTM')
    plt.legend(loc='upper right')
    plt.ylabel('Loss')
    plt.xlabel('Epochs')
    plt.xlim()
    plt.ylim(0)
    #plt.savefig('figure2')
    plt.show()
######################################################################################################################    
predictions, acc_final, loss_final = sess.run([pred_softmax, accuracy, loss], feed_dict={X: X_test, Y: y_test})
print()
print(f'final results: accuracy: {acc_final} loss: {loss_final}')
###################################### confusion matrix ##############################################################
LABELS           = ['Downstairs', 'Jogging', 'Sitting', 'Standing', 'Upstairs', 'Walking']
max_test         = np.argmax(y_test, axis=1)
max_predictions  = np.argmax(predictions, axis=1)
confusion_matrix = metrics.confusion_matrix(max_test, max_predictions)
plt.figure(figsize=(10, 6))
sns.heatmap(confusion_matrix, cmap="Blues", xticklabels=LABELS, yticklabels=LABELS, annot=True, fmt="d");
plt.title("Confusion Matrix for CNN-LSTM")
plt.ylabel('True label')
plt.xlabel('Predicted label')
#plt.savefig('figure3')
plt.show();
#######################################################################################################################
max_test = np.argmax(y_test, axis=1)
max_predictions = np.argmax(predictions, axis=1)
precision = metrics.precision_score(max_test,max_predictions, average='weighted')
print(precision)
recall = metrics.recall_score(max_test,max_predictions, average= 'weighted')
print(recall)
fwscore=metrics.f1_score(max_test, max_predictions,average='weighted')
print(fwscore) # F1 MEASURE SCORE
############################################################# Report ###########################################################
print(metrics.classification_report(max_test, max_predictions, target_names=LABELS, digits=4))
##################################################### ROC CURVES ######################################################
perf=pd.DataFrame([["{0:0.2f}%".format(100*precision_score(max_test, max_predictions, average="micro")), 
                    "{0:0.2f}%".format(100*recall_score(max_test, max_predictions   , average="micro")),
                    "{0:0.2f}%".format(100*f1_score(max_test, max_predictions       , average="micro"))],
                   ["{0:0.2f}%". format(100*precision_score(max_test, max_predictions, average="macro")), 
                    "{0:0.2f}%".format(100*recall_score(max_test,max_predictions    , average="macro")),
                    "{0:0.2f}%".format(100*f1_score(max_test, max_predictions       , average="macro"))]], 
                  index=["Micro Average", "Macro Average"], columns=["Precision", "Recall", "F Score"])
######################################### # Plot all ROC curves #########################################################################
Activity = {
    1: 'Downstairs', 2: 'Jogging', 3: 'Sitting', 4: 'Standing', 5: 'Upstairs', 6: 'Walking' }
fpr = dict()
tpr = dict()
roc_auc = dict()
for i in range(N_CLASSES):
    fpr[i], tpr[i], _ = roc_curve(y_test[:, i], predictions[:, i])
    roc_auc[i] = auc(fpr[i], tpr[i])
#Compute micro-average ROC curve and ROC area under the curve
fpr["micro"], tpr["micro"], _ = roc_curve(y_test.ravel(), predictions.ravel()) 
roc_auc["micro"] = auc(fpr["micro"], tpr["micro"])
all_fpr = np.unique(np.concatenate([fpr[i] for i in range(N_CLASSES)])) # First aggregate all false positive rates
mean_tpr = np.zeros_like(all_fpr) # Then interpolate all ROC curves at this points
for i in range(N_CLASSES):
    mean_tpr += np.interp(all_fpr, fpr[i], tpr[i])
mean_tpr /= N_CLASSES # Finally average it and compute AUC
fpr["macro"] = all_fpr
tpr["macro"] = mean_tpr
roc_auc["macro"] = auc(fpr["macro"], tpr["macro"])
########################################################################################################
plt.style.use('seaborn-whitegrid')
sns.set(style="white", font_scale = 1.5)
plt.figure(figsize=(10,6))
colors = ['deeppink', 'darkorange', 'aqua', "black", "green", "blue"]
for i, color in zip(range(N_CLASSES), colors):
    plt.plot(fpr[i], tpr[i], color=color,
             label='{0} (AUC = {1:0.2f})'
             ''.format(Activity[i+1], roc_auc[i]))
plt.plot([0, 1], [0, 1], color='red', linestyle='--',  linewidth=2, label= 'Random guess') # dashed black = k--
plt.ylim(-0.03,1.04)
plt.xlim(-0.03,1.01)
plt.xlabel ('False Positive Rate')
plt.ylabel ('True Positive Rate')
plt.title  ('ROC Curves for CNN-LSTM')
plt.legend (loc="lower right")
plt.show()
################################################################################################
sess.close()
###################################################################################################
'''
plt.plot(fpr["micro"], tpr["micro"],
         label='micro-average ROC curve (area = {0:0.2f})'
               ''.format(roc_auc["micro"]),
         color='orange', linestyle=':', linewidth=4)
plt.plot(fpr["macro"], tpr["macro"],
         label='macro-average ROC curve (area = {0:0.2f})'
               ''.format(roc_auc["macro"]),
         color='navy', linestyle=':', linewidth=4)
'''




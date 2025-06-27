    
    
const amqp = require('amqplib/callback_api');

const queue = process.argv[2] || 'hello';
const msg = process.argv[3] || 'Hello world';

amqp.connect('amqp://localhost', function(error0, connection) {
if (error0) throw error0;
connection.createChannel(function(error1, channel) {
    if (error1) throw error1;
    channel.assertQueue(queue, { durable: false });
    channel.sendToQueue(queue, Buffer.from(msg));
    console.log(` [x] Sent "${msg}" to queue "${queue}"`);
    setTimeout(() => connection.close(), 500);
});
});
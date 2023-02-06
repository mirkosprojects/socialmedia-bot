var text = ["Let me help you publish messages!",
    "I can even send Whatsapp messages!",
    "Can I post something for you?",
    "Did you try posting to Instagram yet?",
    "Give my developer a star on GitHub! https://github.com/mirkosprojects/socialmedia-bot",
    "Got some stuff to post?",
    "I can help you update your friends!",
    "How can I help you?",
    "Howdy! What's your social media update for the day?",
    "Hi there! What can I help you post today?",
    "Hi, let's create a post together!",
    "Greetings! Let's share a story.",
    "Did you know that I can post Emojis 🚀",
    "Hiya! Got some work for me?",
    "Let's make some social media magic happen 🪄",
    "A post a day keeps the boredom at bay",
    "The early poster catches the most likes",
    "A great photo is worth a thousand likes"];
var elem = document.getElementById("bot_greeting");
var inst;
var temp = [];
var animation_paused = false;

document.addEventListener("visibilitychange", function () {
    if (document.hidden) {
        clearInterval(inst);
    } else {
        inst = setInterval(change_text, 60000);
    }
});

function change_text() {
    if (temp.length == 0) {
        temp = text.slice();
    }
    var counter = Math.floor(Math.random() * temp.length);
    elem.innerHTML = "";
    text_str = temp.splice(counter, 1)[0];
    showText("#bot_greeting", text_str, 0, 30);
}

var showText = function (target, message, index, interval) {
    if (index < message.length) {
        $(target).append(message[index++]);
        setTimeout(function () { showText(target, message, index, interval); }, interval);
    };
}
setTimeout(change_text, 0);
inst = setInterval(change_text, 60000);

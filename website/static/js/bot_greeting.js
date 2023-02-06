import { text, timeout } from "../phrases.js";
var elem = document.getElementById("bot_greeting");
var inst;
var temp = [];

document.addEventListener("visibilitychange", function () {
    if (document.hidden) {
        clearInterval(inst);
    } else {
        inst = setInterval(change_text, timeout);
    }
});

function change_text() {
    if (temp.length == 0) {
        temp = text.slice();
    }
    var counter = Math.floor(Math.random() * temp.length);
    elem.innerHTML = "";
    showText("#bot_greeting", temp.splice(counter, 1)[0], 0, 30);
}

var showText = function (target, message, index, interval) {
    if (index < message.length) {
        $(target).append(message[index++]);
        setTimeout(function () { showText(target, message, index, interval); }, interval);
    };
}
setTimeout(change_text, 0);
inst = setInterval(change_text, timeout);

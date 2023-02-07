import { text, timeout, interval } from "../phrases.js";
var elem = document.getElementById("bot_greeting");
var inst;
var temp = [];

/**
 * Clear/run animation, depending if tab is visible
 */
document.addEventListener("visibilitychange", function () {
    if (document.hidden) {
        clearInterval(inst);
    } else {
        inst = setInterval(change_text, timeout);
    }
});

/**
 * Choose random element and pass it to showText
 */
function change_text() {
    if (temp.length == 0) {
        temp = text.slice();
    }
    var counter = Math.floor(Math.random() * temp.length);
    elem.innerHTML = "";
    var sliced_text = slice_text(temp.splice(counter, 1)[0]);
    showText("#bot_greeting", sliced_text, 0, interval);
}

/**
 * 
 * @param {[string]} target The html id
 * @param {[Array<string>]} message The message to show
 * @param {[number]} index next digit in message (for recursion)
 * @param {[Number]} interval time steps in ms
 */
var showText = function (target, message, index, interval) {
    if (index < message.length) {
        $(target).append(message[index++]);
        setTimeout(function () { showText(target, message, index, interval); }, interval);
    };
}
/**
 * Slices a string into an array of characters and emojis
 * @param {[string]} text_str input string to slice
 * @returns {[Array<string>]} array of characters and emojis
 */
function slice_text(text_str){
    const regex = /\p{Extended_Pictographic}/ug;
    var indexPairs = [];
    var slices = [];
    var matchArr;
    while (null !== (matchArr = regex.exec(text_str))) {
        indexPairs.push([matchArr.index, regex.lastIndex]);
    }
    for (let i=0, i2=0; i<text_str.length; i++) {
        if (i2 < indexPairs.length){
            var indexPair = indexPairs[i2];
            if (i<indexPair[0] || i>indexPair[1]){
                slices.push(text_str[i]);
            }
            else if (i2 < indexPairs.length){
                slices = slices.concat(text_str.slice(indexPair[0], indexPair[1]));
                i2++;
                i = i+indexPair[1]-indexPair[0]-1;
            }
        } else {
                slices.push(text_str[i]);
        }
    }
    return(slices)
}

setTimeout(change_text, 0);
inst = setInterval(change_text, timeout);



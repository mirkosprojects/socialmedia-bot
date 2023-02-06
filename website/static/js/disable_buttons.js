function disableButton() {
    var post_btn = document.getElementById('send_post_button');
    // var upload_button = document.getElementById('upload_button');

    var twt = document.getElementById('twitter');
    var twt1 = document.getElementById('twitter1');
    var wa = document.getElementById('whatsapp');
    var wa1 = document.getElementById('whatsapp1');
    var inst = document.getElementById('instagram');
    var inst1 = document.getElementById('instagram1');
    var fb = document.getElementById('facebook');
    var fb1 = document.getElementById('facebook1');
    var sc = document.getElementById('snapchat');
    var sc1 = document.getElementById('snapchat1');
    var ln = document.getElementById('linkedin');
    var ln1 = document.getElementById('linkedin1');

    post_btn.disabled = true;
    // post_btn.innerText = 'Posting...';
    // upload_button.disabled = true;

    twt.hidden = true;
    twt1.hidden = false;
    wa.hidden = true
    wa1.hidden = false
    inst.hidden = true;
    inst1.hidden = false;
    fb.hidden = true;
    fb1.hidden = false;
    sc.hidden = true;
    sc1.hidden = false;
    ln.hidden = true;
    ln1.hidden = false;

  }
$("input").change(function(e) {    
    var file = e.originalEvent.srcElement.files[0];
    
    var img = document.createElement("img");
    var reader = new FileReader();
    reader.onloadend = function() {
         img.src = reader.result;
    }
    reader.readAsDataURL(file);
    $("img").replaceWith(img)
});
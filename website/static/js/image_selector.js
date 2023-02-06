$("input").change(function (e) {
    var file = e.originalEvent.srcElement.files[0];
    var img = document.getElementById("upload_image")
    var reader = new FileReader();
    reader.onloadend = function () {
      img.src = reader.result;
    }
    reader.readAsDataURL(file);
    $("upload_image").replaceWith(img);
  });
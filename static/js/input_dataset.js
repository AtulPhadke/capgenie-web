document.addEventListener('DOMContentLoaded', () => {
  const inputFolder = document.getElementById('input_folder_icon');
  const img = document.getElementById('info_icon');
  var mask = document.getElementById('mask_screen');
  
  img.addEventListener('click', () => {
      mask.style.visibility = "visible";
  });
  mask.addEventListener('click', () => {
      mask.style.visibility = "hidden";
  });

  inputFolder.addEventListener('click', async () => {
    // For web version, redirect to new dataset page
    window.location.href = '/new_dataset';
  });
}); 
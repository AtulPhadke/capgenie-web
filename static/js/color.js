function hslToHex(h, s, l) {
    s /= 100;
    l /= 100;
  
    const k = n => (n + h / 30) % 12;
    const a = s * Math.min(l, 1 - l);
    const f = n =>
      Math.round(255 * (l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)))));
  
    return `#${[f(0), f(8), f(4)]
      .map(x => x.toString(16).padStart(2, '0'))
      .join('')}`;
  }

  function shuffle(array) {
    let currentIndex = array.length;
  
    
    while (currentIndex != 0) {
      let randomIndex = Math.floor(Math.random() * currentIndex);
      currentIndex--;

      [array[currentIndex], array[randomIndex]] = [
        array[randomIndex], array[currentIndex]];
    }
  }
  
function generateDistinctColors(count) {
    const colors = [];
    const saturation = 90;
    const lightness = 60;
  
    for (let i = 0; i < count; i++) {
      const hue = Math.floor((360 / count) * i);
      colors.push(hslToHex(hue, saturation, lightness));
    }

    shuffle(colors);
  
    return colors;
  } 
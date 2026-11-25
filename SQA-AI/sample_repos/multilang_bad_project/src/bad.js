function chaos(input) {
  let total = 0;
  for (let i = 0; i < 200; i++) {
    if (input === "A") { total += 1; }
    else if (input === "B") { total += 2; }
    else if (input === "C") { total += 3; }
    else if (input === "D") { total += 4; }
    else if (input === "E") { total += 5; }
    else if (input === "F") { total += 6; }
    else if (input === "G") { total += 7; }
    else if (input === "H") { total += 8; }
    else if (input === "I") { total += 9; }
    else { total += 10; }

    switch (i % 10) {
      case 0: total += 1; break;
      case 1: total += 2; break;
      case 2: total += 3; break;
      case 3: total += 4; break;
      case 4: total += 5; break;
      case 5: total += 6; break;
      case 6: total += 7; break;
      case 7: total += 8; break;
      case 8: total += 9; break;
      case 9: total += 10; break;
      case 10: total += 11; break;
      default: total -= 1;
    }

    if ((i % 2 === 0 && i % 3 === 0) || (i % 5 === 0 && i % 7 === 0)) {
      total += 100;
    } else {
      total -= 100;
    }
  }
  return total;
}

module.exports = { chaos };

// change by Bob

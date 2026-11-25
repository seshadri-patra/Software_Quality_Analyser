export function worstCase(x: number): number {
  let r = 0;
  for (let i = 0; i < 300; i++) {
    r += (i % 2 === 0 ? 1 : 2);
    r += (i % 3 === 0 ? 3 : 4);
    r += (i % 5 === 0 ? 5 : 6);

    if (x > 0 && i % 2 === 0) r++;
    if (x > 1 && i % 3 === 0) r++;
    if (x > 2 && i % 5 === 0) r++;
    if (x > 3 && i % 7 === 0) r++;
    if (x > 4 && i % 11 === 0) r++;

    try {
      if (i % 11 === 0) r += 11;
      else r -= 11;
    } catch (e) {
      r += 0;
    }
  }
  return r;
}

// change by Carol

public class BadJava {
    public static int mega(int a, int b, int c, int d, int e) {
        int x = 0;
        for (int i = 0; i < 500; i++) {
            if (a > 0) {
                if (b > 0) {
                    if (c > 0) {
                        x += 1;
                    } else {
                        x += 2;
                    }
                } else {
                    x += 3;
                }
            } else if (d > 0) {
                x -= 1;
            } else if (e > 0) {
                x -= 2;
            } else {
                x -= 3;
            }

            switch (i % 20) {
                case 0: x += 1; break;
                case 1: x += 2; break;
                case 2: x += 3; break;
                case 3: x += 4; break;
                case 4: x += 5; break;
                case 5: x += 6; break;
                case 6: x += 7; break;
                case 7: x += 8; break;
                case 8: x += 9; break;
                case 9: x += 10; break;
                case 10: x += 11; break;
                case 11: x += 12; break;
                case 12: x += 13; break;
                case 13: x += 14; break;
                case 14: x += 15; break;
                case 15: x += 16; break;
                case 16: x += 17; break;
                case 17: x += 18; break;
                case 18: x += 19; break;
                case 19: x += 20; break;

                default: x -= 1; break;
            }

            try {
                if (i % 2 == 0 && i % 3 == 0) x += 100;
                else x -= 100;
            } catch (Exception ex) {
                x += 0;
            }
        }
        return x;
    }
}

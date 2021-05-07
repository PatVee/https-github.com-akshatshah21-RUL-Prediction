from scipy.special import dawsn

from customRTS import CustomRTS
from customKF import CustomKF

class RULPredictor:
    def __init__(self, debug=False):

        self.w = None  # Threshold for failure

        # Initial Parameters (Theta)
        self.η0_bar = 0.0  # Initial mean of drift coefficient
        self.V_η0 = 1.0  # Initial variance of drift coefficient
        self.σ_square = 1.0  # Part of measurement noise variance
        self.Q = 1.0  # Process variance

        self.EM_ITER = 20  # Max iterations for EM

        # Readings
        self.y = [0]
        self.t = [0]
        self.num_samples = 0

        self.z = None  # stores y[i] - y[i-1]
        self.del_t = None  # stores t[i] - t[i-1]

    def reading(self, yi, ti):
        self.y.append(yi)
        self.t.append(ti)

        z.append(self.y[-1] - self.y[-2])
        del_t.append(self.t[-1] - self.t[-2])

        # Update initial parameters
        self.η0_bar, self.V_η0, self.Q, self.σ_square = self.EM()

    def EM(self):
        η_0_bar = self.η0_bar
        P_0 = self.P_0
        Q = self.Q
        σ_square = self.σ_square

        likelihoods = list()

        for k in range(self.EM_ITER):
            rts = customRTS(self.z, self.del_t)
            expected_η, expected_η_square, expected_η_η_1 = rts.run(η_0_bar, P_0, Q, σ_square)

            # E part
            t1 = np.log(P_0)
            t2 = (expected_η_square[0] - 2 * expected_η[0] * η_0_bar + η_0_bar ** 2) / P_0
            t3 = 0
            t4 = 0
            for j in range(1, self.num_samples):
                t3 += np.log(Q) + \
                    (expected_η_square[j] - 2 * expected_η_η_1[j] + expected_η_square[j-1]) / Q
                t4 += np.log(σ_square) + \
                    (self.z[j] ** 2 - 2 * expected_η[j-1] * self.z[j] * self.del_t[j] + \
                        self.del_t[j] ** 2 * expected_η_square[j-1]) / (σ_square * self.del_t[j])
            likelihood = -t1 - t2 - t3 - t4
            likelihoods.append(likelihood)

            # M part
            f3 = 0
            f4 = 0
            for j in range(1, self.num_samples):    
                f3 += (expected_η_square[j] - 2 *
                       expected_η_η_1[j] + expected_η_square[j-1])
                f4 += ((self.z[j] ** 2) - 2*expected_η[j-1] * self.z[j] *
                       self.del_t[j] + (self.del_t[j] **2 )*expected_η_square[j-1]) / self.del_t[j]

            η_0_bar = expected_η[0]
            P_0 = expected_η_square[0] - (expected_η[0] ** 2)
            Q = f3 / self.num_samples
            σ_square = f4 / self.num_samples

            if self.debug:
                print(f"i={self.num_samples} Likelihood: {likelihood}")
                print("eta 0 bar: ", η_0_bar)
                print("P_0: ", P_0)
                print("Q: ", Q)
                print("sigma square: ", σ_square)
                print()

        if self.debug:
            print("likelihoods: ", likelihoods)

            plt.plot(likelihoods)
            plt.xlabel("EM Iteration")
            plt.ylabel("Likelihoods in unknown units")
            plt.grid()
            plt.show()

        return η_0_bar, P_0, Q, σ_square

    def predict_RUL(self):
        kf = customKF(self.Q, self.σ_square)
        η, P = kf.batch_filter(self.η_0_bar, self.P_0, self.z, self.del_t)

        return RULPredictor.calculate_RUL(self.w, η, P, self.y[-1])

    @staticmethod
    def calculate_RUL(w, η, P, y):
        '''
        ( sqrt(2)x(w - y_i) / sqrt(P_i|i) ) x D( η_i_cap / sqrt(2 x P_i|i) )
        '''
        
        try:
            D = dawsn(η / ((2 * P) ** 0.5))
        except:
            print(f"η_cap={η}")
            print(f"P={self.P}")

        rul = abs(((2**0.5) * (w - y) * D)/ (P**0.5))
        
        return rul
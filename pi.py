import time
import inspect
import platform
import jit

def compute_pi(iterations):
    delta = 1.0 / iterations
    inside = 0.0
    x = 0.0
    while x < 1:
        y = 0.0
        while y < 1:
            if x*x + y*y < 1:
                inside = inside + 1
            y = y + delta
        x = x + delta
    total = iterations * iterations
    return inside / total * 4

def run(name, fn, iterations):
    a = time.time()
    pi = fn(iterations)
    b = time.time()
    t = b - a
    print('%10s pi = %.6f    t = %.2f secs' % (name, pi, t))

N = 3000
def main():
    run(platform.python_implementation(), compute_pi, N)
    if platform.python_implementation() != 'PyPy':
        jitted = jit.compile(compute_pi)
        run('JIT', jitted, N)

if __name__ == '__main__':
    main()

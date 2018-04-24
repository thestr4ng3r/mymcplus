
from array import array
from math import tan, radians, sqrt
from OpenGL import GL


class Vector3:
    def __init__(self, x, y, z):
        self.v = array("f", [x, y, z])


    @property
    def x(self):
        return self.v[0]


    @property
    def y(self):
        return self.v[1]


    @property
    def z(self):
        return self.v[2]


    def __getitem__(self, item):
        return self.v[item]


    @property
    def length_sq(self):
        return self.v[0]*self.v[0] \
               + self.v[1]*self.v[1] \
               + self.v[2]*self.v[2]


    @property
    def length(self):
        return sqrt(self.length_sq)


    def __add__(self, other):
        return Vector3(self.v[0] + other[0],
                       self.v[1] + other[1],
                       self.v[2] + other[2])


    def __sub__(self, other):
        return Vector3(self.v[0] - other[0],
                       self.v[1] - other[1],
                       self.v[2] - other[2])


    def __mul__(self, other):
        if other is Vector3:
            return Vector3(self.v[0] * other[0],
                           self.v[1] * other[1],
                           self.v[2] * other[2])
        else:
            return Vector3(self.v[0] * other,
                           self.v[1] * other,
                           self.v[2] * other)


    def __truediv__(self, other):
        if other is Vector3:
            return Vector3(self.v[0] / other[0],
                           self.v[1] / other[1],
                           self.v[2] / other[2])
        else:
            return Vector3(self.v[0] / other,
                           self.v[1] / other,
                           self.v[2] / other)


    @property
    def normalized(self):
        return self / self.length


    def dot(self, other):
        return self.v[0] * other[0] \
               + self.v[1] * other[1] \
               + self.v[2] * other[2]


    def cross(self, other):
        return Vector3(self.v[1] * other[2] - self.v[2] * other[1],
                       self.v[2] * other[0] - self.v[0] * other[2],
                       self.v[0] * other[1] - self.v[1] * other[0])


class Matrix4x4:
    def __init__(self, data):
        if len(data) != 16:
            raise ValueError("data must have exactly length 16.")
        self.m = array("f", data)


    @property
    def ctypes_array(self):
        return (GL.GLfloat * 16)(*self.m)


    def __mul__(self, other):
        m = self.m
        n = other.m
        return Matrix4x4([
            m[0] * n[0]  + m[4] * n[1]  + m[8] * n[2]   + m[12] * n[3],
            m[1] * n[0]  + m[5] * n[1]  + m[9] * n[2]   + m[13] * n[3],
            m[2] * n[0]  + m[6] * n[1]  + m[10] * n[2]  + m[14] * n[3],
            m[3] * n[0]  + m[7] * n[1]  + m[11] * n[2]  + m[15] * n[3],
            m[0] * n[4]  + m[4] * n[5]  + m[8] * n[6]   + m[12] * n[7],
            m[1] * n[4]  + m[5] * n[5]  + m[9] * n[6]   + m[13] * n[7],
            m[2] * n[4]  + m[6] * n[5]  + m[10] * n[6]  + m[14] * n[7],
            m[3] * n[4]  + m[7] * n[5]  + m[11] * n[6]  + m[15] * n[7],
            m[0] * n[8]  + m[4] * n[9]  + m[8] * n[10]  + m[12] * n[11],
            m[1] * n[8]  + m[5] * n[9]  + m[9] * n[10]  + m[13] * n[11],
            m[2] * n[8]  + m[6] * n[9]  + m[10] * n[10] + m[14] * n[11],
            m[3] * n[8]  + m[7] * n[9]  + m[11] * n[10] + m[15] * n[11],
            m[0] * n[12] + m[4] * n[13] + m[8] * n[14]  + m[12] * n[15],
            m[1] * n[12] + m[5] * n[13] + m[9] * n[14]  + m[13] * n[15],
            m[2] * n[12] + m[6] * n[13] + m[10] * n[14] + m[14] * n[15],
            m[3] * n[12] + m[7] * n[13] + m[11] * n[14] + m[15] * n[15]
        ])



    @classmethod
    def perspective(cls, fovy, aspect, near, far):
        f = 1.0 / tan(radians(fovy) / 2.0)
        d = near - far
        return cls([
            f / aspect, 0.0,        0.0,                0.0,
            0.0,        f,          0.0,                0.0,
            0.0,        0.0,        (far+near) / d,     -1.0,
            0.0,        0.0,        2.0*far*near / d,   0.0])


    @classmethod
    def look_at(cls, eye, center, up):
        f = (center - eye).normalized
        u = up.normalized
        s = f.cross(u)
        u = s.normalized.cross(f)
        return cls([
            s[0],       u[0],       -f[0],     0.0,
            s[1],       u[1],       -f[1],     0.0,
            s[2],       u[2],       -f[2],     0.0,
            -eye[0], -eye[1],     -eye[2],     1.0])

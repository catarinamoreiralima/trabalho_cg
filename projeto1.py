import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders
import numpy as np
import glm
import ctypes
import math

glfw.init()
glfw.window_hint(glfw.VISIBLE, glfw.TRUE)

window = glfw.create_window(720,600,"Programa",None,None)

if not window:
    glfw.terminate()

glfw.make_context_current(window)

# ---------------------------------------
# SHADERS
# ---------------------------------------

vertex_code = """
attribute vec3 position;
uniform mat4 mat_transformation;

void main(){
    gl_Position = mat_transformation * vec4(position,1.0);
}
"""

fragment_code = """
uniform vec4 color;

void main(){
    gl_FragColor = color;
}
"""

program = glCreateProgram()

vertex = glCreateShader(GL_VERTEX_SHADER)
fragment = glCreateShader(GL_FRAGMENT_SHADER)

glShaderSource(vertex,vertex_code)
glShaderSource(fragment,fragment_code)

glCompileShader(vertex)
if not glGetShaderiv(vertex,GL_COMPILE_STATUS):
    print(glGetShaderInfoLog(vertex))

glCompileShader(fragment)
if not glGetShaderiv(fragment,GL_COMPILE_STATUS):
    print(glGetShaderInfoLog(fragment))

glAttachShader(program,vertex)
glAttachShader(program,fragment)

glLinkProgram(program)

glUseProgram(program)

# ---------------------------------------
# GEOMETRIA CASA
# ---------------------------------------

cube = [

(-0.1923,-0.20, 0.0897), ( 0.0897,-0.20, 0.1923), ( 0.0897, 0.00, 0.1923),
(-0.1923,-0.20, 0.0897), ( 0.0897, 0.00, 0.1923), (-0.1923, 0.00, 0.0897),

(-0.0897,-0.20,-0.1923), ( 0.1923, 0.00,-0.0897), ( 0.1923,-0.20,-0.0897),
(-0.0897,-0.20,-0.1923), (-0.0897, 0.00,-0.1923), ( 0.1923, 0.00,-0.0897),

(-0.0897,0.00,-0.1923), (-0.1923,0.00,0.0897), (0.0897,0.00,0.1923),
(-0.0897,0.00,-0.1923), (0.0897,0.00,0.1923), (0.1923,0.00,-0.0897),

(-0.0897,-0.20,-0.1923), (0.0897,-0.20,0.1923), (-0.1923,-0.20,0.0897),
(-0.0897,-0.20,-0.1923), (0.1923,-0.20,-0.0897), (0.0897,-0.20,0.1923)
]

cube_sides = [

(-0.0897,-0.20,-0.1923), (-0.1923,-0.20, 0.0897), (-0.1923, 0.00, 0.0897),
(-0.0897,-0.20,-0.1923), (-0.1923, 0.00, 0.0897), (-0.0897, 0.00,-0.1923),

(0.1923,-0.20,-0.0897), (0.0897, 0.00, 0.1923), (0.0897,-0.20, 0.1923),
(0.1923,-0.20,-0.0897), (0.1923, 0.00,-0.0897), (0.0897, 0.00, 0.1923)
]

pyramid = [

(-0.1923,0.00, 0.0897),
( 0.0897,0.00, 0.1923),
( 0.0000,0.15, 0.0000),

( 0.1923,0.00,-0.0897),
(-0.0897,0.00,-0.1923),
( 0.0000,0.15, 0.0000)
]

pyramid_sides = [

( 0.0897,0.00, 0.1923),
( 0.1923,0.00,-0.0897),
( 0.0000,0.15, 0.0000),

(-0.0897,0.00,-0.1923),
(-0.1923,0.00, 0.0897),
( 0.0000,0.15, 0.0000)
]

pyramid_base = [

(-0.1923,0.00, 0.0897),
( 0.0897,0.00, 0.1923),
( 0.1923,0.00,-0.0897),

(-0.1923,0.00, 0.0897),
( 0.1923,0.00,-0.0897),
(-0.0897,0.00,-0.1923)
]

floor = [

# TOP FACE (just below the house)
(-1.0, -0.21, -1.0), ( 1.0, -0.21, -1.0), ( 1.0, -0.21,  1.0),
(-1.0, -0.21, -1.0), ( 1.0, -0.21,  1.0), (-1.0, -0.21,  1.0),

# BOTTOM FACE
(-1.0, -1, -1.0), ( 1.0, -1,  1.0), ( 1.0, -1, -1.0),
(-1.0, -1, -1.0), (-1.0, -1,  1.0), ( 1.0, -1,  1.0),

# FRONT
(-1.0, -1,  1.0), ( 1.0, -0.21,  1.0), ( 1.0, -1,  1.0),
(-1.0, -1,  1.0), (-1.0, -0.21,  1.0), ( 1.0, -0.21,  1.0),

# BACK
(-1.0, -1, -1.0), ( 1.0, -1, -1.0), ( 1.0, -0.21, -1.0),
(-1.0, -1, -1.0), ( 1.0, -0.21, -1.0), (-1.0, -0.21, -1.0),

# LEFT
(-1.0, -1, -1.0), (-1.0, -0.21,  1.0), (-1.0, -1,  1.0),
(-1.0, -1, -1.0), (-1.0, -0.21, -1.0), (-1.0, -0.21,  1.0),
# RIGHT
( 1.0, -1, -1.0), ( 1.0, -0.21,  1.0), ( 1.0, -0.21,  1.0),
( 1.0, -1, -1.0), ( 1.0, -0.21,  1.0), ( 1.0, -0.21, -1.0),
]

walls = cube + cube_sides
roof = pyramid + pyramid_sides + pyramid_base

vertices_walls = np.zeros(len(walls), [("position", np.float32,3)])
vertices_walls["position"] = walls

vertices_roof = np.zeros(len(roof), [("position", np.float32,3)])
vertices_roof["position"] = roof

vertices_floor = np.zeros(len(floor), [("position", np.float32,3)])
vertices_floor["position"] = floor

# ---------------------------------------
# MATRIZES
# ---------------------------------------

def multiplica_matriz(a,b):

    m_a = a.reshape(4,4)
    m_b = b.reshape(4,4)

    m_c = np.dot(m_a,m_b)

    return m_c.reshape(1,16)

# ---------------------------------------
# OBJECT CLASS
# ---------------------------------------

class SceneObject:
    def __init__(self, vertices):
        self.vertices = vertices
        self.vertex_count = len(vertices)

        self.tx = 0
        self.ty = 0
        self.tz = 0

        self.angle = 0
        self.scale = 1

        self.VBO = glGenBuffers(1)

        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    def draw(self):
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glVertexAttribPointer(loc_position, 3, GL_FLOAT, False, stride, offset)

        c = math.cos(self.angle)
        s = math.sin(self.angle)

        mat_rot = np.array([
            c,-s,0,0,
            s,c,0,0,
            0,0,1,0,
            0,0,0,1
        ], np.float32)

        mat_trans = np.array([
            1,0,0,self.tx,
            0,1,0,self.ty,
            0,0,1,self.tz,
            0,0,0,1
        ], np.float32)

        mat_scale = np.array([
            self.scale,0,0,0,
            0,self.scale,0,0,
            0,0,self.scale,0,
            0,0,0,1
        ], np.float32)

        mat_temp = multiplica_matriz(mat_rot, mat_scale)
        mat_final = multiplica_matriz(mat_trans, mat_temp)

        glUniformMatrix4fv(loc_transform, 1, GL_TRUE, mat_final)

        glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)
# ---------------------------------------
# ATTRIBUTOS
# ---------------------------------------

stride = vertices_walls.strides[0]
offset = ctypes.c_void_p(0)

loc_position = glGetAttribLocation(program,"position")
glEnableVertexAttribArray(loc_position)

loc_transform = glGetUniformLocation(program,"mat_transformation")
loc_color = glGetUniformLocation(program,"color")

# ---------------------------------------
# CRIAR OBJETOS
# ---------------------------------------


# house
house_walls = SceneObject(vertices_walls)
house_roof  = SceneObject(vertices_roof)
floor = SceneObject(vertices_floor)


for obj in [house_walls, house_roof, floor]:
    obj.tx = 0


# ---------------------------------------
# OPENGL SETTINGS
# ---------------------------------------

glEnable(GL_DEPTH_TEST)

# ---------------------------------------
# LOOP PRINCIPAL
# ---------------------------------------

while not glfw.window_should_close(window):

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glClearColor(0.5,0.7,1,1)


    house_roof.angle += 0.01
    house_walls.angle += 0.01

    house_walls.ty += 0.001
    house_roof.ty += 0.001

    house_walls.scale *= 0.999
    house_roof.scale *= 0.999

    # desenhar objetos

    # HOUSE
    glUniform4f(loc_color, 0.9, 0.8, 0.4, 1)
    house_walls.draw()

    glUniform4f(loc_color, 0.4, 0.2, 0.1, 1)
    house_roof.draw()

    glUniform4f(loc_color, 0.7, 0.9, 0.4, 1)
    floor.draw()


    glfw.swap_buffers(window)
    glfw.poll_events()

glfw.terminate()
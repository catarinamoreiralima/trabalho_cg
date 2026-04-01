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
# GEOMETRIAS
# ---------------------------------------

def create_grass(x, z, size=0.05):
    vertices = []

    # triângulo 1
    vertices.append((x, -0.21, z))
    vertices.append((x - size/2, size, z))
    vertices.append((x + size/2, size, z))

    # triângulo 2 (cruzado, mais volumoso)
    vertices.append((x, -0.21, z))
    vertices.append((x, size, z - size/2))
    vertices.append((x, size, z + size/2))

    return vertices


def create_flat_sphere(rx, ry, rz, segments=40, rings=20):
    vertices = []

    for i in range(rings):
        phi1 = math.pi * i / rings - math.pi / 2
        phi2 = math.pi * (i + 1) / rings - math.pi / 2

        for j in range(segments):
            theta1 = 2 * math.pi * j / segments
            theta2 = 2 * math.pi * (j + 1) / segments

            # pontos
            p1 = (
                rx * math.cos(phi1) * math.cos(theta1),
                ry * math.sin(phi1),
                rz * math.cos(phi1) * math.sin(theta1)
            )

            p2 = (
                rx * math.cos(phi2) * math.cos(theta1),
                ry * math.sin(phi2),
                rz * math.cos(phi2) * math.sin(theta1)
            )

            p3 = (
                rx * math.cos(phi2) * math.cos(theta2),
                ry * math.sin(phi2),
                rz * math.cos(phi2) * math.sin(theta2)
            )

            p4 = (
                rx * math.cos(phi1) * math.cos(theta2),
                ry * math.sin(phi1),
                rz * math.cos(phi1) * math.sin(theta2)
            )

            # triângulo 1
            vertices.append(p1)
            vertices.append(p2)
            vertices.append(p3)

            # triângulo 2
            vertices.append(p1)
            vertices.append(p3)
            vertices.append(p4)

    return vertices

def create_dome(radius, height, segments=40, rings=10):
    vertices = []

    for i in range(rings):
        phi1 = (math.pi / 2) * i / rings
        phi2 = (math.pi / 2) * (i + 1) / rings

        y1 = height * math.sin(phi1)
        y2 = height * math.sin(phi2)

        r1 = radius * math.cos(phi1)
        r2 = radius * math.cos(phi2)

        for j in range(segments):
            theta1 = 2 * math.pi * j / segments
            theta2 = 2 * math.pi * (j + 1) / segments

            # triângulo 1
            vertices.append((r1 * math.cos(theta1), y1, r1 * math.sin(theta1)))
            vertices.append((r2 * math.cos(theta1), y2, r2 * math.sin(theta1)))
            vertices.append((r2 * math.cos(theta2), y2, r2 * math.sin(theta2)))

            # triângulo 2
            vertices.append((r1 * math.cos(theta1), y1, r1 * math.sin(theta1)))
            vertices.append((r2 * math.cos(theta2), y2, r2 * math.sin(theta2)))
            vertices.append((r1 * math.cos(theta2), y1, r1 * math.sin(theta2)))

    return vertices

def create_truncated_cone(r_bottom, r_top, height, segments=40):
    vertices = []

    y_bottom = -height / 2
    y_top = height / 2

    for i in range(segments):
        theta1 = 2 * math.pi * i / segments
        theta2 = 2 * math.pi * (i + 1) / segments

        # pontos base inferior
        b1 = (r_bottom * math.cos(theta1), y_bottom, r_bottom * math.sin(theta1))
        b2 = (r_bottom * math.cos(theta2), y_bottom, r_bottom * math.sin(theta2))

        # pontos base superior
        t1 = (r_top * math.cos(theta1), y_top, r_top * math.sin(theta1))
        t2 = (r_top * math.cos(theta2), y_top, r_top * math.sin(theta2))

        # -----------------
        # LATERAIS
        # -----------------
        # triângulo 1
        vertices.append(b1)
        vertices.append(t1)
        vertices.append(t2)

        # triângulo 2
        vertices.append(b1)
        vertices.append(t2)
        vertices.append(b2)

        # -----------------
        # BASE INFERIOR
        # -----------------
        vertices.append((0, y_bottom, 0))
        vertices.append(b2)
        vertices.append(b1)

        # -----------------
        # BASE SUPERIOR
        # -----------------
        vertices.append((0, y_top, 0))
        vertices.append(t1)
        vertices.append(t2)

    return vertices

#laser de abdução
laser = create_truncated_cone(0.1, 0.05, 0.5, segments=40)
vertices_laser = np.zeros(len(laser), [("position", np.float32,3)])
vertices_laser["position"] = laser

#ufo
oval = create_flat_sphere(0.5, 0.15, 0.5)
dome = create_dome(0.2, 0.1, segments=40, rings=10)

vertices_oval = np.zeros(len(oval), [("position", np.float32,3)])
vertices_oval["position"] = oval

vertices_top = np.zeros(len(dome), [("position", np.float32,3)])
vertices_top["position"] = dome


#grama
grass_vertices = []

for i in range(100):  # quantidade de gramas
    x = np.random.uniform(-1, 1)
    z = np.random.uniform(-1, 1)

    grass_vertices += create_grass(x, z, size=0.05)

vertices_grass = np.zeros(len(grass_vertices), [("position", np.float32,3)])
vertices_grass["position"] = grass_vertices



cube = [

(-0.20,-0.20, 0.00), ( 0.00,-0.20, 0.20), ( 0.00, 0.00, 0.20),
(-0.20,-0.20, 0.0897), ( 0.0897, 0.00, 0.20), (-0.20, 0.00, 0.00),

(-0.00,-0.20,-0.20), ( 0.20, 0.00,-0.00), ( 0.20,-0.20,-0.00),
(-0.00,-0.20,-0.20), (-0.00, 0.00,-0.20), ( 0.20, 0.00,-0.00),

(-0.00,0.00,-0.20), (-0.20,0.00,0.00), (0.00, 0.00,0.20),
(-0.00 ,0.00,-0.20), (0.00 ,0.00,0.20), (0.20 ,0.00, -0.00),

(-0.00,-0.20,-0.20), (0.00,-0.20,0.20), (-0.20,-0.20,0.00),
(-0.00,-0.20,-0.20), (0.20,-0.20,-0.00), (0.00,-0.20,0.20)
]

cube_sides = [

(-0.00,-0.20,-0.20), (-0.20,-0.20, 0.00), (-0.20, 0.00, 0.00),
(-0.00,-0.20,-0.20), (-0.20, 0.00, 0.00), (-0.00, 0.00,-0.20),

( 0.20,-0.20,-0.00), ( 0.00,-0.20, 0.20), ( 0.00, 0.00, 0.20),
( 0.20,-0.20,-0.00), ( 0.00, 0.00, 0.20), ( 0.20, 0.00,-0.00)

]

pyramid = [

(-0.20,0.00, 0.00), ( 0.00,0.00, 0.20), ( 0.00,0.15, 0.0000),

( 0.20,0.00,-0.00),
(-0.0,0.00,-0.20),
( 0.0000,0.15, 0.0000)
]

pyramid_sides = [

( 0.0,0.00, 0.20),
( 0.20,0.00,-0.00),
( 0.0000,0.15, 0.0000),

(-0.00,0.00,-0.20),
(-0.20,0.00, 0.00),
( 0.0000,0.15, 0.0000)
]

pyramid_base = [

(-0.20,0.00, 0.00),
( 0.00,0.00, 0.20),
( 0.20,0.00,-0.00),

(-0.20,0.00, 0.00),
( 0.20,0.00,-0.00),
(-0.0,0.00,-0.20)
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

#casa

walls = cube + cube_sides
roof = pyramid + pyramid_sides + pyramid_base

vertices_walls = np.zeros(len(walls), [("position", np.float32,3)])
vertices_walls["position"] = walls

vertices_roof = np.zeros(len(roof), [("position", np.float32,3)])
vertices_roof["position"] = roof

vertices_floor = np.zeros(len(floor), [("position", np.float32,3)])
vertices_floor["position"] = floor

# nuvem
oval_nuvem1 = create_flat_sphere(0.8, 0.8, 0.8)
oval_nuvem2 = create_flat_sphere(0.6, 0.6, 0.6)
oval_nuvem3 = create_flat_sphere(0.7, 0.7, 0.7)

oval_nuvem1_vertices = np.zeros(len(oval_nuvem1), [("position", np.float32,3)])
oval_nuvem1_vertices["position"] = oval_nuvem1  

oval_nuvem2_vertices = np.zeros(len(oval_nuvem2), [("position", np.float32,3)])
oval_nuvem2_vertices["position"] = oval_nuvem2  

oval_nuvem3_vertices = np.zeros(len(oval_nuvem3), [("position", np.float32,3)])
oval_nuvem3_vertices["position"] = oval_nuvem3


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

ufo_base = SceneObject(vertices_oval)
ufo_top = SceneObject(vertices_top)


object_nuvem1 = SceneObject(oval_nuvem1_vertices)
object_nuvem2 = SceneObject(oval_nuvem2_vertices)
object_nuvem3 = SceneObject(oval_nuvem3_vertices)

object_laser = SceneObject(vertices_laser)

for obj in [house_walls, house_roof, floor, ufo_base, ufo_top]:
    obj.tx = 0


# ---------------------------------------
# OPENGL SETTINGS
# ---------------------------------------

glEnable(GL_DEPTH_TEST)
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

# ---------------------------------------
# LOOP PRINCIPAL
# ---------------------------------------

time = 0

object_nuvem1.tx = -1
object_nuvem2.tx = -0.7
object_nuvem3.tx = -0.4

wireframe = False

def key_event(window, key, scancode, action, mods):
    global wireframe
    if action == glfw.PRESS or action == glfw.REPEAT:

        #wireframe

        if key == glfw.KEY_P:
            wireframe = not wireframe

        #nuvens
        # mover para esquerda (A)
        if key == glfw.KEY_A:
            object_nuvem1.tx -= 0.05
            object_nuvem2.tx -= 0.05
            object_nuvem3.tx -= 0.05

        # mover para direita (D)
        if key == glfw.KEY_D:
            object_nuvem1.tx += 0.05
            object_nuvem2.tx += 0.05
            object_nuvem3.tx += 0.05

        # UFO + laser

        # movimento lateral (Q esquerda, E direita)
        if glfw.get_key(window, glfw.KEY_Q) == glfw.PRESS:
            ufo_base.tx -= 0.02
            ufo_top.tx  -= 0.02
            object_laser.tx -= 0.02

        if glfw.get_key(window, glfw.KEY_E) == glfw.PRESS:
            ufo_base.tx += 0.02
            ufo_top.tx  += 0.02
            object_laser.tx += 0.02

        # casa

        # movimento vertical (I sobe, J desce)
        if glfw.get_key(window, glfw.KEY_I) == glfw.PRESS:
            house_walls.ty += 0.02
            house_roof.ty  += 0.02

        if glfw.get_key(window, glfw.KEY_J) == glfw.PRESS:
            house_walls.ty -= 0.02
            house_roof.ty  -= 0.02


        # rotação (O horário, U anti-horário)
        if glfw.get_key(window, glfw.KEY_O) == glfw.PRESS:
            house_walls.angle -= 0.02
            house_roof.angle  -= 0.02

        if glfw.get_key(window, glfw.KEY_U) == glfw.PRESS:
            house_walls.angle += 0.02
            house_roof.angle  += 0.02


        # escala (X aumenta, Z diminui)
        if glfw.get_key(window, glfw.KEY_X) == glfw.PRESS:
            house_walls.scale += 0.01
            house_roof.scale  += 0.01

        if glfw.get_key(window, glfw.KEY_Z) == glfw.PRESS:
            house_walls.scale -= 0.01
            house_roof.scale  -= 0.01




while not glfw.window_should_close(window):

    glfw.set_key_callback(window, key_event)

    time += 0.02

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glClearColor(0.5,0.7,1,1)



    ##POSICIONAMENTO E BALANÇO DO UFO

    ufo_base.tz = -0.5
    ufo_base.scale = 0.8

    ufo_top.tz = -0.6
    ufo_top.scale = 0.8


    # movimento vertical (flutuar)
    ufo_base.ty = 0.8 + 0.05 * math.sin(time)
    ufo_top.ty  = 0.9 + 0.05 * math.sin(time)

    # leve inclinação (balançando)
    ufo_base.angle = 0.2 * math.sin(time)
    ufo_top.angle  = 0.2 * math.sin(time)

    #MOVIMENTO DAS NUVENS

    object_nuvem1.ty = 0.8 + 0.1 * math.sin(time * 0.3)
    object_nuvem1.scale = 0.4
    object_nuvem1.tz = 1

    object_nuvem2.ty = 0.8 + 0.1 * math.sin(time * 0.3 + 1)
    object_nuvem2.scale = 0.4
    object_nuvem2.tz = 1

    object_nuvem3.ty = 0.8 + 0.1 * math.sin(time * 0.3 + 2)
    object_nuvem3.scale = 0.4
    object_nuvem3.tz = 1



    # WIREFRAME 

    if wireframe:
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    else:
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    # OBJETOS:

    #CASA
    glUniform4f(loc_color, 0.9, 0.8, 0.4, 1)
    house_walls.draw()

    glUniform4f(loc_color, 0.4, 0.2, 0.1, 1)
    house_roof.draw()

    glUniform4f(loc_color, 0.7, 0.9, 0.4, 1)
    floor.draw()


    #UFO
    glUniform4f(loc_color, 0.651, 0.651, 0.635, 1)
    ufo_base.draw()

    glUniform4f(loc_color, 0.412, 0.412, 0.4, 1)
    ufo_top.draw()

    #NUVENS

    glUniform4f(loc_color, 0.9, 0.9, 0.9, 1)
    object_nuvem1.draw()   

    glUniform4f(loc_color, 0.87, 0.87, 0.87, 1)
    object_nuvem2.draw()  

    glUniform4f(loc_color, 0.85, 0.85, 0.85, 1)  
    object_nuvem3.draw()

    #LASER
    glUniform4f(loc_color,0.031, 1, 0.345, 0.5)
    object_laser.scale = 3
    object_laser.draw()


    


    glfw.swap_buffers(window)
    glfw.poll_events()

glfw.terminate()
bl_info = {
    "name":         "ZED Model",
    "author":       "Rico Tyrell",
    "blender":      ( 2, 6, 2 ),
    "version":      ( 0, 0, 1 ),
    "location":     "File > Import-Export",
    "description":  "Export as a ZED model",
    "category":     "Import-Export"
}

import bpy
import struct;
from bpy_extras.io_utils import ExportHelper

def menu_func( self, context ):
    self.layout.operator( Exporter.bl_idname, text="ZED Model Format (.zed)" );

def register( ):
    bpy.utils.register_module( __name__ );
    bpy.types.INFO_MT_file_export.append( menu_func );
    
def unregister( ):
    bpy.utils.unregister_module( __name__ );
    bpy.types.INFO_MT_file_export.remove( menu_func );

if __name__ == "__main__":
    register( )
    
class ZEDFileHeader:
    numVertices = 0;
    numIndices = 0;
    fileSize = 0;
    
    def __init__( self, numVertices, numIndices ):
        self.numVertices = numVertices;
        self.numIndices = numIndices;
    
    def write( self, file ):
        #file.write( "Size: %d | Vertices: %d | Indices: %d\n" % ( self.sizeInBytes, self.numVertices, self.numIndices ) );
        file.write( struct.pack( 'cccc', b'Z', b'E', b'D', b'M' ) );
        file.write( struct.pack( 'BBB', 0, 0, 1 ) );
        file.write( struct.pack( 'BBBB', 0, 0, 0, 0 ) );

class ZEDFileBody:
    mesh = None;
    tri_list = [ ];
    
    def __init__( self, mesh ):
        self.mesh = mesh;
    
    def write( self, file ):
        for vert in self.mesh.vertices:
            x, y, z = vert.co;
            #file.write( 'Vertex: %f %f %f\n' % (x, y, z ) );#( vert.co[ 0 ], vert.co[ 1 ], vert.co[ 2 ] ) );
            file.write( struct.pack( 'fff', vert.co[ 0 ], vert.co[ 1 ], vert.co[ 2 ] ) );
        for tri in self.tri_list:
            x, y, z = tri.vertex_indices;
            #file.write( 'Index: %d %d %d\n' % ( x, y, z ) );#( tri.vertex_indices[ 0 ], tri.vertex_indices[ 1 ], tri.vertex_indixes[ 2 ] ) );
            file.write( struct.pack( 'hhh', tri.vertex_indices[ 0 ], tri.vertex_indices[ 1 ], tri.vertex_indices[ 2 ] ) );

class TriangleWrapper( object ):
    __slots__ = "vertex_indices", "offset";
    
    def __init__( self, vertex_index=( 0, 0, 0 ) ):
        self.vertex_indices = vertex_index;

class Exporter( bpy.types.Operator, ExportHelper ):
    bl_idname   = "untitled.zed";
    bl_label    = "Export ZED";
    bl_options  = {'PRESET'};
    
    filename_ext    = ".zed";
    
    def extract_triangles( self, mesh ):
        triangle_list = [ ];
        
        for face in mesh.polygons:
            face_verts = face.vertices;
            if len( face.vertices ) == 3:
                vert = mesh.vertices[ index ];
                new_tri = TriangleWrapper( ( face_verts[ 0 ], face_verts[ 1 ], face_verts[ 2 ] ) );
            else:
                new_tri_1 = TriangleWrapper( ( face_verts[ 0 ], face_verts[ 1 ], face_verts[ 2 ] ) );
                new_tri_2 = TriangleWrapper( ( face_verts[ 0 ], face_verts[ 2 ], face_verts[ 3 ] ) );
                triangle_list.append( new_tri_1 );
                triangle_list.append( new_tri_2 );
        return triangle_list;
    
    def execute( self, context ):
        bpy.ops.object.mode_set( mode='OBJECT' );
        
        result = { 'FINISHED' };
        
        ob = context.object;
        if not ob or ob.type != 'MESH':
            raise NameError( "Cannot export: object %s is not a mesh" % ob );
            
        fileBody = ZEDFileBody( ob.data );
        fileBody.tri_list = self.extract_triangles( fileBody.mesh );
        
        fileHeader = ZEDFileHeader(
            len( fileBody.mesh.vertices ),
            len( fileBody.tri_list ) * 3 );
        
        file = open( self.filepath, 'wb' );#, encoding='utf8' );
        fileHeader.write( file );
        fileBody.write( file );
        WriteModelMetaChunk( fileBody.mesh, file, len( fileBody.tri_list )*3, len( fileBody.tri_list ) );
        file.close( );
        return result;

def WriteModelMetaChunk( Mesh, File, IndexCount, TriCount ):
    File.write( struct.pack( "I", len( Mesh.vertices ) ) );
    File.write( struct.pack( "I", IndexCount ) );
    # Only one mesh, must look into exporting all meshes...
    File.write( struct.pack( "I", 1 ) );
    # No materials right now...
    File.write( struct.pack( "I", 0 ) );
    File.write( struct.pack( "cccc", b'C', b'u', b'b', b'e' ) );
    for x in range( 0, 60 ):
        File.write( struct.pack( "c", b'\0' ) );
    # No strips
    File.write( struct.pack( "II", 0, 0 ) );
    # Lists
    File.write( struct.pack( "II", TriCount, TriCount ) );
    # No fans
    File.write( struct.pack( "II", 0, 0 ) );
    File.write( struct.pack( "BBB", 0, 0, 1 ) );

    
#def WriteVertexChunks( ):
    
#def WriteMeshChunks( ):

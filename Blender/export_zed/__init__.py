bl_info = {
    "name":         "0 ZED Model",
    "author":       "Open Game Developers",
    "blender":      ( 2, 6, 2 ),
    "version":      ( 0, 0, 1 ),
    "location":     "File > Import-Export",
    "description":  "Export as a ZED model",
    "category":     "Import-Export"
}

import bpy;
import struct;
import io;
import os;
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
    register( );
    
class ZEDFileHeader:
    numVertices = 0;
    numIndices = 0;
    fileSize = 0;
    
    def __init__( self, numVertices, numIndices ):
        self.numVertices = numVertices;
        self.numIndices = numIndices;
    
    def write( self, file ):
        file.write( struct.pack( '<cccc', b'Z', b'E', b'D', b'M' ) );
        file.write( struct.pack( '<BBB', 0, 0, 1 ) );
        file.write( struct.pack( '<BBBB', 0, 0, 0, 0 ) );

class ZEDFileBody:
    mesh = None;
    tri_list = [ ];
    
    def __init__( self, mesh ):
        self.mesh = mesh;
    
    def write( self, file ):
        for vert in self.mesh.vertices:
            x, y, z = vert.co;
            file.write( struct.pack( 'fff', vert.co[ 0 ], vert.co[ 1 ], vert.co[ 2 ] ) );
        for tri in self.tri_list:
            x, y, z = tri.vertex_indices;
            file.write( struct.pack( 'hhh', tri.vertex_indices[ 0 ], tri.vertex_indices[ 1 ], tri.vertex_indices[ 2 ] ) );

class TriangleWrapper( object ):
    __slots__ = "vertex_indices", "offset";
    
    def __init__( self, vertex_index=( 0, 0, 0 ) ):
        self.vertex_indices = vertex_index;

class Exporter( bpy.types.Operator, ExportHelper ):
    bl_idname   = "untitled.zed";
    bl_label    = "Export ZED";
    bl_options  = {'PRESET'};
    mesh_list   = [ ];
    
    filename_ext    = ".zed";
    
    def extract_triangles( self, mesh ):
        triangle_list = [ ];

        return triangle_list;
    
    def execute( self, context ):
        del self.mesh_list[ 0:len( self.mesh_list ) ];
        bpy.ops.object.mode_set( mode='OBJECT' );
        
        result = { 'FINISHED' };
        
        for object in bpy.data.objects:
            if object.type == 'MESH':
                self.mesh_list.append( object );
        
        fileHeader = ZEDFileHeader( len( self.mesh_list[ 0 ].data.vertices ),
            0 );
        
        file = open( self.filepath, 'wb' );
        fileHeader.write( file );
        WriteModelMetaChunk( file, self.mesh_list, 0, 0 );
        for mesh in self.mesh_list:
            WriteMeshChunks( file, mesh );
        WriteChunkEnd( file );
        file.close( );
        return result;

def WriteModelMetaChunk( File, MeshList, IndexCount, TriCount ):
    File.write( struct.pack( "<H", 0x0002 ) );
    File.write( struct.pack( "<I", 0 ) );
    FileSize = 0;
    File.write( struct.pack( "<I", len( MeshList[ 0 ].data.vertices ) ) );
    FileSize += 4;
    File.write( struct.pack( "<I", IndexCount ) );
    FileSize += 4;
    File.write( struct.pack( "<I", len( MeshList ) ) );
    FileSize += 4;
    # No materials right now...
    File.write( struct.pack( "<I", 0 ) );
    FileSize += 4;
    File.write( struct.pack( "<cccc", b'C', b'u', b'b', b'e' ) );
    for x in range( 0, 60 ):
        File.write( struct.pack( "<c", b'\0' ) );
    FileSize += 64;
    # No strips
    File.write( struct.pack( "<II", 0, 0 ) );
    FileSize += 8;
    # Lists
    File.write( struct.pack( "<II", TriCount, TriCount ) );
    FileSize += 8;
    # No fans
    File.write( struct.pack( "<II", 0, 0 ) );
    FileSize += 8;
    File.write( struct.pack( "<BBB", 0, 0, 1 ) );
    FileSize += 3;
    File.seek( -( FileSize+4 ), 1 );
    File.write( struct.pack( "<I", FileSize ) );
    File.seek( FileSize, 1 );
    WriteChunkEnd( File );
    
def WriteMeshChunks( File, Mesh ):
    File.write( struct.pack( "<H", 0x0004 ) );
    File.write( struct.pack( "<I", 0 ) );
    FileSize = 0;
    # Vertex Count
    File.write( struct.pack( "<I", len( Mesh.data.vertices ) ) );
    FileSize += 4;
    # Material ID
    File.write( struct.pack( "<I", 0 ) );
    FileSize += 4;
    # Strips
    File.write( struct.pack( "<I", 0 ) );
    FileSize += 4;
    # Lists
    File.write( struct.pack( "<I", 1 ) );
    FileSize += 4;
    # Fans
    File.write( struct.pack( "<I", 0 ) );
    FileSize += 4;
    # Write out vertices...
    for vert in Mesh.data.vertices:
        # Get the world matrix to transform the vertices by before exporting them
        Co = Mesh.matrix_world * vert.co;
        File.write( struct.pack( "<fff", Co[ 0 ], Co[ 2 ], -Co[ 1 ] ) );
        File.write( struct.pack( "<fff", vert.normal[ 0 ], vert.normal[ 2 ], -vert.normal[ 1 ] ) );
        FileSize += 24;
    # Write out strips, lists, and fans (only lists will be output for now)
    # Amount of indices in list array
    File.write( struct.pack( "<H", 0 ) );
    FileSize += 2;
    IndexOffset = 0;
    IndexCount = 0;
    for face in Mesh.data.polygons:
        face_verts = face.vertices;
        if len( face.vertices ) == 3:
            File.write( struct.pack( "<HHH", face_verts[ 2 ], face_verts[ 1 ], face_verts[ 0 ] ) );
            FileSize += 6;
            IndexOffset += 6;
            IndexCount += 3;
        else:
            File.write( struct.pack( "<HHH", face_verts[ 2 ], face_verts[ 1 ], face_verts[ 0 ] ) );
            File.write( struct.pack( "<HHH", face_verts[ 3 ], face_verts[ 2 ], face_verts[ 0 ] ) );
            FileSize += 12;
            IndexOffset += 12;
            IndexCount += 6;
    File.seek( -( IndexOffset+2 ), 1 );
    File.write( struct.pack( "<H", IndexCount ) );
    File.seek( IndexOffset, 1 );    
    File.seek( -( FileSize+4 ), 1 );
    File.write( struct.pack( "<I", FileSize ) );
    File.seek( FileSize, 1 );
    WriteChunkEnd( File );

def WriteChunkEnd( File ):
    File.write( struct.pack( "<HI", 0xFFFF, 0 ) );

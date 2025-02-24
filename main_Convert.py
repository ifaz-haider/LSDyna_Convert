#!/usr/bin/env python3
"""
Example script to convert an Abaqus .inp mesh (nodes + elements + sets) 
into an LS-DYNA DUALCESE-style .k file.

Usage:
    python inp_to_lsdyna.py mesh_euler.inp output.k
"""

import sys
import pandas as pd
import numpy as np
import pdb
import config

def parse_inp(inp_file):
    """
    Parse a simple Abaqus .inp file containing nodes/elements/nsets/elsets.
    
    Returns:
        nodes       (dict): { node_id: (x, y, z) }
        elements    (dict): { elem_id: [node1, node2, ..., node8], 'type': 'C3D8R' }
        nsets       (dict): { set_name: [node_ids...] }
        elsets      (dict): { set_name: [elem_ids...] }
        surfaces    (dict): { surf_name: [ [elm id, "SX"]] }   # 
    """
    nodes = {}
    elements = {}
    nsets = {}
    elsets = {}
    surfaces = {}

    reading_nodes = False
    reading_elements = False
    current_elset_name = None
    current_nset_name = None
    current_surf_name = None

    # In Abaqus .inp, lines that start with '*' are keywords;
    # lines that follow (until the next '*') are data lines for that keyword.
    with open(inp_file, 'r') as f:
        for line in f:
            line_stripped = line.strip()
            # Skip blank lines or comments (if any)
            if not line_stripped or line_stripped.startswith('**'):
                continue

            # Check for keyword lines
            if line_stripped.startswith('*'):
                reading_nodes = False
                reading_elements = False

                # Lowercase for safer checks
                lower_line = line_stripped.lower()

                # 1) *Node
                if lower_line.startswith('*node'):
                    reading_nodes = True

                # 2) *Element, e.g. *Element, type=C3D8R
                elif lower_line.startswith('*element'):
                    reading_elements = True
                    # You could parse the element type if needed, e.g.:
                    #   element_type = ...
                    #   Actually parse from "type=C3D8R" in the line if you have different types
                    # For demonstration we'll just store 'C3D8R' or 'UNKNOWN'
                    # or you can store it in a variable to reuse
                    if 'type=' in lower_line:
                        eq_idx = lower_line.index('type=')
                        elem_type_str = lower_line[eq_idx+5:].replace(',', '').replace(' ', '')
                    else:
                        elem_type_str = 'UNKNOWN'
                    # We might store different element arrays per type,
                    # but for demonstration we'll keep them all in `elements`.

                # 3) *Nset
                elif lower_line.startswith('*nset'):
                    # parse name from the line, e.g. *Nset, nset=SETNAME
                    # example: "*Nset, nset=MYNODESET"
                    name = None
                    if 'nset=' in lower_line:
                        start = lower_line.index('nset=') + len('nset=')
                        # read until comma or end
                        rest = lower_line[start:].split(',')[0]
                        name = rest.strip().upper()
                    if name:
                        current_nset_name = name
                        nsets.setdefault(name, [])
                        current_elset_name = None
                        current_surf_name = None
                    else:
                        current_nset_name = None

                # 4) *Elset
                elif lower_line.startswith('*elset'):
                    # parse name from the line, e.g. *Elset, elset=EULER_ELEMS
                    name = None
                    if 'elset=' in lower_line:
                        start = lower_line.index('elset=') + len('elset=')
                        rest = lower_line[start:].split(',')[0]
                        name = rest.strip().upper()
                    if name:
                        current_elset_name = name
                        elsets.setdefault(name, [])
                        current_nset_name = None
                        current_surf_name = None
                    else:
                        current_elset_name = None

                # 5) *Surface
                elif lower_line.startswith('*surface'):
                    # parse name, e.g. *Surface, name=SOMESURF, type=ELEMENT
                    # Surfaces can be more complex. We'll do a placeholder:
                    name = None
                    if 'name=' in lower_line:
                        start = lower_line.index('name=') + len('name=')
                        rest = lower_line[start:].split(',')[0]
                        name = rest.strip().upper()
                    if name:
                        current_surf_name = name
                        surfaces.setdefault(name, [])
                        current_elset_name = None
                        current_nset_name = None
                    else:
                        name = None
                    # you might need to store more info (type=ELEMENT, etc.)
                    # We'll skip details for brevity.
                continue

            # If we are reading node lines
            if reading_nodes:
                # Node line typically:  ID, X, Y, Z
                # e.g. "      1, 0.0, 0.0, 0.0"
                parts = line_stripped.split(',')
                if len(parts) >= 4:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    z = float(parts[3])
                    nodes[nid] = (x, y, z)

            # If we are reading element lines
            elif reading_elements:
                # For a hex (C3D8) in Abaqus: ID, n1, n2, n3, n4, n5, n6, n7, n8
                parts = line_stripped.split(',')
                # Typically 9 entries: [elem_id, node1, node2, ..., node8]
                if len(parts) >= 9:
                    eid = int(parts[0])
                    conn = [int(p) for p in parts[1:9]]
                    elements[eid] = conn

            # If we have a current_nset_name, lines may contain node IDs (space- or comma-separated)
            if current_nset_name is not None and line_stripped and not line_stripped.startswith('*'):
                # Node sets in .inp can be comma separated or continued lines
                # e.g. " 1, 2, 3, 4," across multiple lines
                
                #ids = [int(x) for x in line_stripped.replace(',', ' ').split()]

                ids = []
                for x in line_stripped.replace(',', ' ').split():
                    if x:
                        #print(x)
                        ids.append(int(x))

                nsets[current_nset_name].extend(ids)

            # If we have a current_elset_name, lines may contain element IDs
            if current_elset_name is not None and line_stripped and not line_stripped.startswith('*'):
                ids = [int(x) for x in line_stripped.replace(',', ' ').split()]
                elsets[current_elset_name].extend(ids)

            # if we have a surface name, lines may contain surface defintions
            if current_surf_name is not None and line_stripped and not line_stripped.startswith('*'):
                [id, surf] = line_stripped.split(',')
                surfaces[current_surf_name].append([int(id), surf])
                tmp=0

    return nodes, elements, nsets, elsets, surfaces

def write_k(k_file, nodes, elements, nsets, elsets, surfaces):
    """
    Write a minimal LS-DYNA DUALCESE-style .k file:
      *KEYWORD
      *NODE
         ...
      *ELEMENT_SOLID
         ...
      *SET_NODE_LIST (for each nset)
      *SET_ELEMENT_LIST (for each elset)
      *END

    Adjust spacing/format as needed to match your 'fluid_mesh1.k' example.
    """
    with open(k_file, 'w') as f:
        # Header
        #f.write("*KEYWORD\n")

        # --- NODE block ---
        f.write("*DUALCESE_NODE3D\n")
        # LSDYNA free format example: ID, X, Y, Z
        #  (some users prefer fixed columns, e.g. 8 columns wide)
        for nid in sorted(nodes.keys()):
            x, y, z = nodes[nid]
            # Adjust format if your example uses different spacing
            f.write("{:d}, {:g}, {:g}, {:g}, {:g}, {:g}\n".format(nid, x, y, z,0,0))

        # --- ELEMENT_SOLID block ---
        # LSDYNA format: EID, PID, n1, n2, ..., n8
        # For a single-part fluid domain, we can just pick PID=1
        pid = 1
        f.write("*DUALCESE_ELE3D\n")
        for eid in sorted(elements.keys()):
            conn = elements[eid]
            # Typically 8 nodes for a hex
            # If you have other types, handle them as needed
            if len(conn) == 8:
                f.write(f"{eid}, {pid}")
                for nn in conn:
                    f.write(", {:d}".format(nn))
                f.write("\n")
            else:
                # If you need to handle different topologies, do so here
                pass

        # --- Node sets ---
        for set_name, node_list in nsets.items():
            f.write("$ Node set: {}\n".format(set_name))
            
            f.write("*DUALCESE_NODESET\n")
            curid = config.nodeset_ssid[set_name]
            f.write(f"       {curid}\n")
            
            # chunk them in lines of (for example) 8 per line
            sorted_nodeset = sorted(set(node_list))  # remove dupes, sort
            chunk_size = 8
            for i in range(0, len(sorted_nodeset), chunk_size):
                chunk = sorted_nodeset[i:i+chunk_size]
                f.write(", ".join(str(n) for n in chunk) + "\n")


        def get_surface_nodes(elements, elmid, faceid):
            curelm = elements[elmid]
            curnodes = config.abq_surf_def[faceid]      
            curnodes = [i-1 for i in curnodes] # 1 based to 0 based indexing
            return [curelm[i] for i in curnodes]
        

        #---- Surface sets ---
        for set_name, surf_list in surfaces.items():
            f.write("$ Surface set: {}\n".format(set_name))
            
            f.write("*DUALCESE_SEGMENTSET\n")
            curid = config.segmentset_ssid[set_name]
            f.write(f"       {curid}\n")
            
            for surf in surf_list:
                elmid = surf[0]
                faceid = surf[1]
                curnodes = get_surface_nodes(elements, elmid, faceid)
                f.write(f"{curnodes[0]}, {curnodes[1]}, {curnodes[2]}, {curnodes[3]},0.0,0.0,0.0,0.0\n")            

        # --- Element sets ---
        # If your example uses e.g. '*SET_ELEMENT_LIST_TITLE', adapt accordingly
        for set_name, elem_list in elsets.items():
            f.write("$ Element set: {}\n".format(set_name))
            
            
            f.write("*DUALCESE_ELEMENTSET\n")
            curid = config.elementset_ssid[set_name]
            f.write(f"      {curid}\n")

            sorted_elemset = sorted(set(elem_list))
            chunk_size = 8
            for i in range(0, len(sorted_elemset), chunk_size):
                chunk = sorted_elemset[i:i+chunk_size]
                f.write(", ".join(str(e) for e in chunk) + "\n")

        # If needed: surface definitions -> *SET_SEGMENT, etc.
        #  We'll skip for brevity.

        # Footer
        f.write("*END\n")


def main():
    # if len(sys.argv) < 3:
    #     print("Usage: python inp_to_lsdyna.py <mesh_euler.inp> <output.k>")
    #     sys.exit(1)

    # 1) Parse .inp
    nodes, elements, nsets, elsets, surfaces = parse_inp(config.inp_file)

    # 2) Write LSDYNA .k
    write_k(config.k_file, nodes, elements, nsets, elsets, surfaces)

    print("Conversion complete. Output written to", config.k_file)

if __name__ == "__main__":
    main()
 

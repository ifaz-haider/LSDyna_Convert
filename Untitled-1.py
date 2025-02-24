#!/usr/bin/env python3
"""
Convert an Abaqus .inp mesh into a minimal LS-DYNA DUALCESE-style .k file.

Usage:
    python inp_to_lsdyna.py mesh_euler.inp fluid_mesh1.k
"""

import sys

def parse_inp(inp_file):
    """
    Parse a simple Abaqus .inp file containing nodes/elements/nsets/elsets.
    
    Returns:
        nodes       (dict): { node_id: (x, y, z) }
        elements    (dict): { elem_id: [node1, node2, ..., node8] }
        nsets       (dict): { set_name: [node_ids...] }
        elsets      (dict): { set_name: [elem_ids...] }
        surfaces    (dict): { surf_name: [...] }  # placeholder, not processed here
    """
    nodes = {}
    elements = {}
    nsets = {}
    elsets = {}
    surfaces = {}

    reading_nodes = False
    reading_elements = False
    current_nset_name = None
    current_elset_name = None

    with open(inp_file, 'r') as f:
        for line in f:
            line_stripped = line.strip()
            # Skip blank lines or comments (Abaqus style: '**')
            if not line_stripped or line_stripped.startswith('**'):
                continue

            # Check for keyword line
            if line_stripped.startswith('*'):
                # Reset reading flags
                reading_nodes = False
                reading_elements = False

                lower_line = line_stripped.lower()

                # *Node
                if lower_line.startswith('*node'):
                    reading_nodes = True
                    current_nset_name = None
                    current_elset_name = None
                    continue

                # *Element
                if lower_line.startswith('*element'):
                    reading_elements = True
                    current_nset_name = None
                    current_elset_name = None
                    continue

                # *Nset
                if lower_line.startswith('*nset'):
                    # parse name, e.g. *Nset, nset=XYZ
                    name = None
                    if 'nset=' in lower_line:
                        start = lower_line.index('nset=') + len('nset=')
                        rest = lower_line[start:].split(',')[0]
                        name = rest.strip().upper()
                    if name:
                        current_nset_name = name
                        nsets.setdefault(name, [])
                    else:
                        current_nset_name = None
                    continue

                # *Elset
                if lower_line.startswith('*elset'):
                    # parse name, e.g. *Elset, elset=XYZ
                    name = None
                    if 'elset=' in lower_line:
                        start = lower_line.index('elset=') + len('elset=')
                        rest = lower_line[start:].split(',')[0]
                        name = rest.strip().upper()
                    if name:
                        current_elset_name = name
                        elsets.setdefault(name, [])
                    else:
                        current_elset_name = None
                    continue

                # *Surface
                if lower_line.startswith('*surface'):
                    # parse surface name if present
                    name = None
                    if 'name=' in lower_line:
                        start = lower_line.index('name=') + len('name=')
                        rest = lower_line[start:].split(',')[0]
                        name = rest.strip().upper()
                    if name:
                        surfaces.setdefault(name, [])
                    continue

                # For any other keyword, just skip
                continue

            # -----------------------------
            # If reading node lines
            # -----------------------------
            if reading_nodes:
                parts = line_stripped.split(',')
                if len(parts) >= 4:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    z = float(parts[3])
                    nodes[nid] = (x, y, z)

            # -----------------------------
            # If reading element lines
            # -----------------------------
            elif reading_elements:
                parts = line_stripped.split(',')
                if len(parts) > 1:
                    eid = int(parts[0])
                    # For a hex (C3D8) => 1 + 8 node IDs
                    # If it’s a different element type, adapt accordingly
                    conn = [int(p) for p in parts[1:]]
                    elements[eid] = conn

            # -----------------------------
            # If lines belong to *Nset
            # -----------------------------
            if current_nset_name is not None and not line_stripped.startswith('*'):
                # collect node IDs from line
                ids = [int(x) for x in line_stripped.replace(',', ' ').split()]
                nsets[current_nset_name].extend(ids)

            # -----------------------------
            # If lines belong to *Elset
            # -----------------------------
            if current_elset_name is not None and not line_stripped.startswith('*'):
                # collect element IDs from line
                ids = [int(x) for x in line_stripped.replace(',', ' ').split()]
                elsets[current_elset_name].extend(ids)

    return nodes, elements, nsets, elsets, surfaces





def main():
    if len(sys.argv) < 3:
        print("Usage: python inp_to_lsdyna.py <mesh_euler.inp> <fluid_mesh1.k>")
        sys.exit(1)

    inp_file = sys.argv[1]
    k_file   = sys.argv[2]

    # Parse the Abaqus inp file
    nodes, elements, nsets, elsets, surfaces = parse_inp(inp_file)

    # Write the LS-DYNA DUALCESE-style k file
    write_k(k_file, nodes, elements, nsets, elsets, surfaces)

    print(f"Conversion complete. Output written to: {k_file}")


if __name__ == "__main__":
    main()

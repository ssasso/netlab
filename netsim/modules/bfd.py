#
# BFD transformation module
#
# Contains routines used by routing protocol modules to adjust node/link BFD state
#
import typing

from box import Box

from . import _Module

class BFD(_Module):
  pass

def bfd_link_state(node: Box,proto: str) -> None:
  if not proto in node:
    return
  if not 'bfd' in node[proto]:
    return
  if not 'links' in node:
    return

  node[proto].bfd = True if node[proto].bfd else False   # Convert protocol-level BFD setting into Boolean

  for l in node.links:
    if not proto in l:                     # No protocol-specific link parameters?
      l[proto] = {}                        # ... start with an empty dictionary

    if not 'bfd' in l[proto]:              # No BFD protocol-specific parameters?
      l[proto].bfd = node[proto].bfd       # ... copy from node value and move on

    p = l[proto]
    disable_bfd = False
    disable_bfd = disable_bfd or ('bfd' in l and not l.bfd)     # BFD is disabled on the interface
    disable_bfd = disable_bfd or ('bfd' in p and not p.bfd)
    if disable_bfd:
      l[proto].pop('bfd',None)

    if not l[proto]:
      l.pop(proto,None)

def multiprotocol_bfd_link_state(node: Box,proto: str) -> None:
  if not proto in node:
    return
  if not 'bfd' in node[proto]:
    return

  # Transform boolean BFD routing protocol state into per-AF-state
  #
  if isinstance(node[proto].bfd,bool):
    if node[proto].bfd:
      node[proto].bfd = {} 
      for af in ('ipv4','ipv6'):
        if af in node[proto]:
          node[proto].bfd[af] = True
    else:
      node[proto].bfd = {}

  if not 'links' in node:
    return

  for l in node.links:
    if not proto in l:                     # No protocol-specific link parameters?
      l[proto] = {}                        # ... start with an empty dictionary

    if not 'bfd' in l[proto]:              # No BFD protocol-specific parameters?
      l[proto].bfd = node[proto].bfd       # ... copy from node value and move on

    p = l[proto]                           # Check whether BFD is disabled
    disable_bfd = False
    disable_bfd = disable_bfd or ('bfd' in l and not l.bfd)  # either on the interface
    disable_bfd = disable_bfd or ('bfd' in p and not p.bfd)  # ... or in protocol setting

    if disable_bfd:                        # If BFD is disabled
      l[proto].pop('bfd',None)             # ... remove all BFD protocol parameters
    else:
      if isinstance(l[proto].bfd,bool):    # Otherwise if we had 'bfd: True'
        l[proto].bfd = node[proto].bfd     # ... then copy node data into interface data

    if 'bfd' in l[proto]:                  # AF cleanup
      for af in ('ipv4','ipv6'):
        if not af in l:                    # Remove AF from proto.bfd if it's not enabled on the interface
          l[proto].bfd.pop(af,'None')
      if not l[proto].bfd:                 # If there's nothing left...
        l[proto].pop('bfd',None)           # ... remove proto.bfd dictionary

    if not l[proto]:                       # Last check: if we didn't get any useful protocol data
      l.pop(proto,None)                    # ... remove protocol data from the interface
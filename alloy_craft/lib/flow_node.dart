import 'package:flutter/material.dart';

class FlowNode {
  final String id;
  final String label;
  final IconData icon;
  final String? parentId;
  final List<FlowNode> children;

  FlowNode({
    required this.id,
    required this.label,
    required this.icon,
    this.parentId,
    List<FlowNode>? children, // nullable parametre
  }) : children =
            children != null ? List.from(children) : []; // 🔧 Dinamik liste
}

List<FlowNode> buildTree(List<FlowNode> flatList) {
  Map<String, FlowNode> map = {
    for (var node in flatList)
      node.id: FlowNode(
        id: node.id,
        label: node.label,
        icon: node.icon,
        parentId: node.parentId,
        children: [],
      )
  };

  List<FlowNode> roots = [];

  for (var node in flatList) {
    if (node.parentId == null) {
      roots.add(map[node.id]!);
    } else {
      final parent = map[node.parentId];
      if (parent != null) {
        map[parent.id]!.children.add(map[node.id]!);
      }
    }
  }

  return roots;
}

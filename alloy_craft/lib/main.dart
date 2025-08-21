import 'dart:convert';

import 'package:alloy_craft/binary_phase_display.dart';
import 'package:alloy_craft/faz_grafik_ekrani.dart';
import 'package:alloy_craft/flow_node.dart';
import 'package:alloy_craft/save_load.dart';
import 'package:alloy_craft/ternary_display.dart';
import 'package:flutter/material.dart';
import 'package:flutter_vector_icons/flutter_vector_icons.dart';
import 'package:split_view/split_view.dart';
import 'faz_webview_ekrani.dart';
import 'periodic_table.dart';
import 'faz_input_page.dart';
import 'binary_phase_display.dart';
import 'single_point_display.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Alloy Craft',
      debugShowCheckedModeBanner: false,
      home: HomePage(),
    );
  }
}

List<Map<String, dynamic>> phasePoints = [];

class HomePage extends StatefulWidget {
  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  late SplitViewController rightPanelController;
  @override
  void initState() {
    super.initState();
    nodes.add(
      FlowNode(
        id: 'root',
        label: 'My Project',
        icon: Icons.folder,
        parentId: null,
      ),
    );
    rightPanelController = SplitViewController(
      weights: [0.7, 0.3],
      limits: [null, WeightLimit(min: 0.2, max: 0.7)],
    );
  }

  Map<String, dynamic>? binaryPhaseResult;
  List<Map<String, dynamic>> inputElements = []; // Çoklu element listesi
  String compositionType = 'binary';
  void handleBinaryCalculation(Map<String, dynamic> result) {
    setState(() {
      binaryPhaseResult = result;
    });
  }

  void onBinaryDataReady(
      String element, double temp, double wt, Map<String, dynamic> result) {
    setState(() {
      binaryPhaseResult = result;
      rightPanelController.weights = [0.5, 0.5];
    });
  }

  void addSinglePointFlow() {
    // Kaç tane definer var? → yatay pozisyonu hesapla
    final flowIndex =
        nodes.where((n) => n.label.startsWith('System Definer')).length;

    final baseX = 40.0 + flowIndex * 160.0; // 🔵 X sürekli artıyor (sağa)
    final baseY = 60.0; // 🔵 Y sabit → tüm bloklar üstten başlıyor

    final flowId = DateTime.now().millisecondsSinceEpoch.toString();

    final defId = 'def-$flowId';
    final calcId = 'calc-$flowId';
    final plotId = 'plot-$flowId';

    setState(() {
      nodes.addAll([
        FlowNode(
          id: defId,
          label: "System Definer ${flowIndex + 1}",
          icon: Icons.extension,
          parentId: 'root',
        ),
        FlowNode(
          id: calcId,
          label: "Equilibrium Calculator ${flowIndex + 1}",
          icon: Icons.calculate,
          parentId: defId,
        ),
        FlowNode(
          id: plotId,
          label: "Plot Renderer ${flowIndex + 1}",
          icon: Icons.show_chart,
          parentId: calcId,
        ),
      ]);
    });
  }

  List<FlowNode> flowTree = []; // 🌳 Dinamik ağaç yapısı
  void addNewProjectWithChildren(String solute) {
    final projectId = 'proj_${DateTime.now().millisecondsSinceEpoch}';
    final projectLabel = 'Fe-$solute Project';

    final newProject = FlowNode(
      id: projectId,
      label: projectLabel,
      icon: Icons.folder,
      parentId: null,
      children: [
        FlowNode(
          id: '${projectId}_sys',
          label: 'Alloy Selector',
          icon: Icons.grid_view,
          parentId: projectId,
        ),
        FlowNode(
          id: '${projectId}_eq',
          label: 'Alloy Equilibrium Engine',
          icon: Icons.calculate,
          parentId: projectId,
        ),
        FlowNode(
          id: '${projectId}_vis',
          label: 'Output Viewer',
          icon: Icons.bar_chart,
          parentId: projectId,
        ),
      ],
    );

    setState(() {
      flowTree.add(newProject);
    });
  }

  String selectedMode = '';
  String? selectedElement;
  bool showInputForm = false;
  Map<String, dynamic>? calculationResult;

  String inputSolute = "";
  double inputTemp = 1000.0; // sabit
  double inputWtX = 0.0;
  bool showPhaseDiagram = false;

  void handleElementSelected(String element) {
    setState(() {
      selectedElement = element;
      showInputForm = true;
    });
  }

  void handleCalculationCompleted(Map<String, dynamic> data) {
    setState(() {
      if (selectedMode == 'binary_phase') {
        binaryPhaseResult = data;
      } else if (selectedMode == 'ternary') {
        calculationResult = data;
        if (data.containsKey('elements')) {
          inputElements = List<Map<String, dynamic>>.from(data['elements']);
        }
        if (data.containsKey('temperature')) {
          inputTemp = data['temperature'].toDouble();
        }
      } else {
        // Single point calculation için veriyi işle
        if (data.containsKey('result') && data['result'] != null) {
          calculationResult = data['result'];
        } else {
          calculationResult = data;
        }

        // ÇOK ÖNEMLİ: Çoklu element verilerini kaydet
        if (data.containsKey('elements')) {
          inputElements = List<Map<String, dynamic>>.from(data['elements']);
          compositionType = data['composition_type'] ?? 'multi_element';
        }

        // Sıcaklık bilgisini kaydet
        if (data.containsKey('temperature')) {
          inputTemp = data['temperature'];
        }
      }
      rightPanelController.weights = [0.5, 0.5];
    });
  }

  final GlobalKey<PeriyodikTabloPageState> periyodikTabloKey = GlobalKey();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("Alloy Craft"),
        actions: [
          IconButton(
            icon: Icon(Icons.save),
            tooltip: "Kaydet",
            onPressed: () async {
              await saveAlloyWithPicker();
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text("✅ Proje kaydedildi")),
              );
            },
          ),
          IconButton(
            icon: Icon(Icons.folder_open),
            tooltip: "Yükle",
            onPressed: () async {
              final result = await loadAlloyWithPicker();
              if (periyodikTabloKey.currentState != null) {
                periyodikTabloKey.currentState!.initFromProjectData();
              }
              if (result != null) {
                setState(() {
                  // 1️⃣ Hesaplama verileri
                  inputSolute = result['selected_element'];
                  inputTemp = result['temperature'];
                  inputWtX = result['elements'].firstWhere(
                      (e) => e['symbol'] == inputSolute)['weight_percent'];
                  calculationResult = result['sonuclar'];

                  // 2️⃣ Akış (flow)
                  nodes = (result['akis'] as List)
                      .map((e) => FlowNode(
                            id: e['id'],
                            label: e['label'],
                            icon: IconData(e['icon'],
                                fontFamily: 'MaterialIcons'),
                            parentId: e['parentId'],
                          ))
                      .toList();

                  // 3️⃣ UI modlarını güncelle
                  selectedMode = 'single_point';
                  showInputForm = true;
                });

                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text("📥 Proje yüklendi")),
                );
              }
            },
          ),
        ],
      ),
      drawer: _buildDrawer(),
      body: SplitView(
        viewMode: SplitViewMode.Horizontal,
        indicator: SplitIndicator(viewMode: SplitViewMode.Horizontal),
        controller: SplitViewController(
          weights: [0.15, 0.85], // Sol %25, orta+sağ %75
          limits: [null, WeightLimit(min: 0.65, max: 0.85)],
        ),
        activeIndicator: SplitIndicator(
          viewMode: SplitViewMode.Horizontal,
          isActive: true,
        ),
        children: [
          _buildLeftPanel(),
          SplitView(
            viewMode: SplitViewMode.Horizontal,
            indicator: SplitIndicator(viewMode: SplitViewMode.Horizontal),
            controller: rightPanelController,
            activeIndicator: SplitIndicator(
              viewMode: SplitViewMode.Horizontal,
              isActive: true,
            ),
            children: [
              _buildCenterPanel(),
              _buildRightPanel(),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildLeftPanel() {
    return _buildProjectPanel();
  }

  List<FlowNode> nodes = []; // HomePage state'ine EKLE

  Widget _buildProjectPanel() {
    return Container(
      color: Colors.grey.shade200,
      padding: EdgeInsets.all(8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("📁 Projects",
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
          SizedBox(height: 8),
          Expanded(
            child: ListView.builder(
              itemCount: flowTree.length,
              itemBuilder: (context, index) {
                final parentNode = flowTree[index];
                return Theme(
                  data: ThemeData().copyWith(dividerColor: Colors.transparent),
                  child: ExpansionTile(
                    tilePadding: EdgeInsets.symmetric(horizontal: 8),
                    childrenPadding: EdgeInsets.only(left: 20),
                    leading: Icon(Icons.folder, size: 18),
                    title: Text(
                      parentNode.label,
                      style:
                          TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
                    ),
                    children: parentNode.children.map((child) {
                      return ListTile(
                        dense: true,
                        contentPadding: EdgeInsets.symmetric(horizontal: 8),
                        leading: Icon(child.icon, size: 16),
                        title:
                            Text(child.label, style: TextStyle(fontSize: 12)),
                        onTap: () {
                          if (child.label == 'Equilibrium') {
                            setState(() {
                              selectedMode = 'single_point';
                              showInputForm = false;
                              calculationResult = null;
                            });
                          }
                        },
                      );
                    }).toList(),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTreeNode(FlowNode node) {
    if (node.children.isEmpty) {
      return ListTile(
        leading: Icon(node.icon),
        title: Text(node.label),
        onTap: () {
          setState(() {
            selectedMode = node.id;
          });
        },
      );
    } else {
      return ExpansionTile(
        leading: Icon(node.icon),
        title: Text(node.label),
        children: node.children.map((child) => _buildTreeNode(child)).toList(),
      );
    }
  }

  Widget _buildSchedulerPanel() {
    return Container(
      color: Colors.grey.shade300,
      padding: EdgeInsets.all(8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("📅 Scheduler", style: TextStyle(fontWeight: FontWeight.bold)),
          SizedBox(height: 8),
          ListTile(
            leading: Icon(Icons.schedule),
            title: Text("Scheduled Jobs"),
            onTap: () {},
          ),
        ],
      ),
    );
  }

  Widget _buildRightPanel() {
    return Container(
      padding: EdgeInsets.all(12),
      color: Colors.grey.shade100,
      child: Material(
        color: Colors.transparent,
        child: selectedMode == 'binary_phase' && binaryPhaseResult != null
            ? BinaryPhaseDisplay(result: binaryPhaseResult!)
            : selectedMode == 'single_point' && calculationResult != null
                ? SinglePointDisplay(
                    result: calculationResult!,
                    solute: inputSolute,
                    temperature: inputTemp,
                    weightPercent: inputWtX,
                    sessionId: calculationResult?['session_id'],
                    elements:
                        inputElements, // 🔹 Çoklu element listesi buradan gider
                  )
                : selectedMode == 'ternary' && calculationResult != null
                    ? TernaryDisplay(
                        result: calculationResult!,
                        elements: inputElements, // Bu boş olabilir
                        temperature:
                            inputTemp, // Bu da varsayılan değerde kalabilir
                      ) // YENİ
                    : Center(
                        child: Text("Hesaplama Sonuçları Burada Gözükecek")),
      ),
    );
  }

  Widget _buildCenterPanel() {
    if (selectedMode == 'binary_phase') {
      return OrtaPanelSekmeleri(
        mode: 'binary_phase', // BUNU EKLEYİN
        onElementSelected: handleElementSelected,
        onCalculationComplete: handleCalculationCompleted,
        onAllDataReady: (solute, temp, wt, result) {
          setState(() {
            binaryPhaseResult = result;
            rightPanelController.weights = [0.5, 0.5];
          });
        },
      );
    } else if (selectedMode == 'single_point') {
      // BU BLOK EKSİK
      return OrtaPanelSekmeleri(
        mode: 'single_point',
        onElementSelected: handleElementSelected,
        onCalculationComplete: handleCalculationCompleted,
        onAllDataReady: (solute, temp, wt, result) {
          setState(() {
            inputSolute = solute;
            inputTemp = temp;
            inputWtX = wt;
            calculationResult = result;
            rightPanelController.weights = [0.4, 0.6];
          });
        },
      );
    } else if (selectedMode == 'ternary') {
      return OrtaPanelSekmeleri(
        mode: 'ternary',
        onElementSelected: handleElementSelected,
        onCalculationComplete: handleCalculationCompleted,
        onAllDataReady: (solute, temp, wt, result) {
          setState(() {
            // Ternary sonuçlarını işle
            calculationResult = result;
            rightPanelController.weights = [0.4, 0.6];
          });
        },
      );
    }

    // Ana menü (hiçbir seçim yapılmadığında görünen panel)
    return SingleChildScrollView(
      child: Padding(
        padding: EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("Configuration",
                style: TextStyle(fontWeight: FontWeight.bold)),
            SizedBox(height: 6),
            _sectionTitle("Getting Started"),
            _iconGrid([
              _iconButton(Icons.auto_mode, "Quick Start", () {}),
              _iconButton(Icons.play_circle_outline, "Getting Started", () {}),
              _iconButton(Icons.video_library, "Video Tutorials", () {}),
              _iconButton(Icons.help_outline, "Online Help", () {}),
              _iconButton(Icons.insert_drive_file, "Example Files", () {}),
            ]),
            SizedBox(height: 12),
            _sectionTitle("Modules"),
            _iconGrid([
              _iconButton(Icons.flash_on, "Single Point", () {
                setState(() {
                  selectedMode = 'single_point';
                  selectedElement = null;
                  showInputForm = false;
                  calculationResult = null;
                });
                addSinglePointFlow();
              }),
              _iconButton(Icons.bar_chart, "Show Graphs", () {}),
              _iconButton(Icons.table_chart, "Binary Phase Diagram", () {
                setState(() {
                  selectedMode = 'binary_phase';
                  selectedElement = null;
                  showInputForm = false;
                  calculationResult = null;
                });
              }),
              _iconButton(Icons.change_history, "Ternary Phase Diagram", () {
                setState(() {
                  selectedMode = 'ternary';
                  selectedElement = null;
                  showInputForm = false;
                  calculationResult = null;
                });
              }),
              _iconButton(Icons.calculate, "Calculation", () {}),
              _iconButton(Icons.scatter_plot, "Scheil Solidification", () {}),
              _iconButton(Icons.scale, "Liquidus/Solidus", () {}),
            ]),
          ],
        ),
      ),
    );
  }

  Widget _menuButton(IconData icon, String label, VoidCallback onPressed) {
    return ElevatedButton(
      onPressed: onPressed,
      style: ElevatedButton.styleFrom(
        backgroundColor: Colors.orange.shade300,
        padding: EdgeInsets.all(16),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 36, color: Colors.black87),
          SizedBox(height: 8),
          Text(label, style: TextStyle(color: Colors.black)),
        ],
      ),
    );
  }

  Widget _buildDrawer() {
    return Drawer(
      child: ListView(
        children: [
          DrawerHeader(
            decoration: BoxDecoration(color: Colors.orange),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                CircleAvatar(radius: 30, backgroundColor: Colors.white),
                SizedBox(height: 8),
                Text("Alloy Craft", style: TextStyle(color: Colors.white)),
              ],
            ),
          ),
          ListTile(
            leading: Icon(MaterialCommunityIcons.home),
            title: Text("Ana Sayfa"),
            onTap: () {
              setState(() {
                selectedMode = '';
                selectedElement = null;
                showInputForm = false;
                calculationResult = null;
              });
              Navigator.pop(context);
            },
          ),
          ListTile(
            leading: Icon(MaterialCommunityIcons.flask_outline),
            title: Text("Termodinamik"),
            onTap: () {
              setState(() {
                selectedMode = '';
                selectedElement = null;
                showInputForm = false;
                calculationResult = null;
              });
              Navigator.pop(context);
            },
          ),
          ListTile(
            leading: Icon(MaterialCommunityIcons.arrow_split_vertical),
            title: Text("Difüzyon"),
            onTap: () {
              setState(() {
                selectedMode = '';
                selectedElement = null;
                showInputForm = false;
                calculationResult = null;
              });
              Navigator.pop(context);
            },
          ),
          ListTile(
            leading: Icon(MaterialCommunityIcons.snowflake),
            title: Text("Katılaşma"),
            onTap: () {
              setState(() {
                selectedMode = '';
                selectedElement = null;
                showInputForm = false;
                calculationResult = null;
              });
              Navigator.pop(context);
            },
          ),
          ListTile(
            leading: Icon(MaterialCommunityIcons.brain),
            title: Text("AI Integration"),
            onTap: () {
              setState(() {
                selectedMode = '';
                selectedElement = null;
                showInputForm = false;
                calculationResult = null;
              });
              Navigator.pop(context);
            },
          ),
        ],
      ),
    );
  }
}

Widget _sectionTitle(String title) {
  return Padding(
    padding: const EdgeInsets.symmetric(vertical: 12.0),
    child: Text(title,
        style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
  );
}

Widget _iconGrid(List<Widget> children) {
  return Wrap(
    spacing: 12,
    runSpacing: 12,
    children: children.map((child) {
      return SizedBox(
        width: 100, // 🔒 SABİT GENİŞLİK
        height: 100, // 🔒 SABİT YÜKSEKLİK
        child: child,
      );
    }).toList(),
  );
}

Widget _iconButton(IconData icon, String label, VoidCallback onTap) {
  return GestureDetector(
    onTap: onTap,
    child: Container(
      decoration: BoxDecoration(
        color: Colors.orange.shade100,
        borderRadius: BorderRadius.circular(6), // köşe yumuşaklığı biraz azaldı
        border: Border.all(color: Colors.orange.shade300),
      ),
      padding: EdgeInsets.all(6), // iç boşluk azaltıldı
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 36, color: Colors.black87), // simge boyutu küçüldü
          SizedBox(height: 6),
          Text(label,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12)), // yazı boyutu küçüldü
        ],
      ),
    ),
  );
}

class OrtaPanelSekmeleri extends StatefulWidget {
  final String mode; // YENİ
  final Function(String) onElementSelected;
  final Function(Map<String, dynamic>) onCalculationComplete;

  final Function(String, double, double, Map<String, dynamic>)
      onAllDataReady; // ✅ EKLE

  const OrtaPanelSekmeleri({
    required this.mode,
    required this.onElementSelected,
    required this.onCalculationComplete,
    required this.onAllDataReady, // ✅ EKLE
  });
  @override
  State<OrtaPanelSekmeleri> createState() => _OrtaPanelSekmeleriState();
}

class _OrtaPanelSekmeleriState extends State<OrtaPanelSekmeleri>
    with TickerProviderStateMixin {
  late final TabController _tabController;
  Map<String, dynamic>? calculationResult;

  String inputSolute = "";
  double inputTemp = 1000.0; // sabit
  double inputWtX = 0.0;

  final List<String> tabs = [
    'Elements',
    'Phases',
    'Description',
  ];

  @override
  void initState() {
    _tabController = TabController(length: tabs.length, vsync: this);
    super.initState();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  final GlobalKey<PeriyodikTabloPageState> periyodikTabloKey = GlobalKey();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Sekme çubuğu
        Container(
          color: Colors.grey.shade100,
          child: TabBar(
            controller: _tabController,
            isScrollable: false,
            indicatorColor: Colors.lightBlue,
            labelColor: Colors.black,
            unselectedLabelColor: Colors.grey.shade700,
            labelStyle: TextStyle(fontWeight: FontWeight.w500),
            tabs: tabs.map((label) => Tab(text: label)).toList(),
          ),
        ),
        // Sekme içeriği
        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: [
              // 1. Tab = ELEMENTS
              PeriyodikTabloPage(
                key: periyodikTabloKey,
                source: widget.mode,
                onElementSelected: (element) {
                  setState(() {
                    inputSolute = element;
                  });
                },
                onCalculationComplete: (data) {
                  print("🎯 onCalculationComplete çalıştı.");
                  print("→ result: ${data['result']}");
                  print("→ solute: ${data['solute']}");

                  // selectedMode ve binaryPhaseResult'a erişemezsiniz burada
                  // Direkt widget.onCalculationComplete'i çağırın
                  widget.onCalculationComplete(data);
                },
              ),
              // Diğer sekmeler
              Center(child: Text("Phases")),
              Center(child: Text("Description")),
            ],
          ),
        ),
      ],
    );
  }
}

Widget _buildFlowNode(String label, IconData icon, VoidCallback? onTap) {
  return GestureDetector(
    onTap: onTap,
    child: Container(
      margin: EdgeInsets.symmetric(horizontal: 8),
      padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: Colors.orange),
        boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 2)],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 18, color: Colors.black87),
          SizedBox(width: 6),
          Text(label, style: TextStyle(fontSize: 13)),
        ],
      ),
    ),
  );
}

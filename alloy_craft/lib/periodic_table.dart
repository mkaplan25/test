import 'dart:convert';
import 'package:alloy_craft/save_load.dart';
import 'package:alloy_craft/single_point_display.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;

class PeriyodikTabloPage extends StatefulWidget {
  final String source;
  final Function(String) onElementSelected;
  final Function(Map<String, dynamic>) onCalculationComplete;

  const PeriyodikTabloPage({
    Key? key,
    required this.source,
    required this.onElementSelected,
    required this.onCalculationComplete,
  }) : super(key: key);

  @override
  PeriyodikTabloPageState createState() => PeriyodikTabloPageState();
}

class PeriyodikTabloPageState extends State<PeriyodikTabloPage> {
  String selectedTernaryType = "isothermal"; // Varsayılan olarak vertical
  final TextEditingController tempMinController =
      TextEditingController(text: '300');
  final TextEditingController tempMaxController =
      TextEditingController(text: '1800');
  List<ElementData> elements = [];
  String? userSelectedElement;
  final String fixedElement = 'FE';
  final List<String> selectableElements = [
    'CR',
    'MN',
    'C',
    'NI',
    'MO',
    'V',
    'TI',
    'AL',
    'CU',
    'SI',
    'W',
    'NB'
  ];
// Element kompozisyon için controller'lar
  Map<String, TextEditingController> elementControllers = {};
  // Çoklu element için yeni değişkenler
  List<Map<String, dynamic>> selectedElements = [
    {'symbol': 'FE', 'weight_percent': 100.0, 'is_fixed': true}
  ];

  final TextEditingController controller1 = TextEditingController();
  final TextEditingController controller2 = TextEditingController();
  bool showConditionInputs = false;
  bool showCompositionInputs = false;
  final tempController = TextEditingController(text: '1000.0');
  final pressureController = TextEditingController(text: '100000.0');
  final sizeController = TextEditingController(text: '1.0');
  String selectedTempUnit = "Kelvin";
  String selectedpreUnit = "Pascal";
  String selectedsizeUnit = "Mole";
  bool showBinaryConfig = false;

  bool _isLoading = false;
  String? _errorMessage;
  final String _multiElementUrl =
      'http://127.0.0.1:8000/multi-element-calculation';
  final String _singlePointUrl =
      'http://127.0.0.1:8000/single-point-calculation';
  final String _backendUrl = 'http://127.0.0.1:8000/phase-diagram';
  final String _binaryUrl = 'http://127.0.0.1:8000/binary-phase-diagram';
  String selectedXAxisType = "mol";
  String selectedYAxisType = "celsius";

  void initFromProjectData() {
    if (currentProjectData.containsKey("selected_element") &&
        currentProjectData.containsKey("elements")) {
      final selected = currentProjectData["selected_element"];
      final elements = currentProjectData["elements"] as List;

      final fe = elements.firstWhere((e) => e["symbol"] == "FE",
          orElse: () => {"weight_percent": 100});
      final x = elements.firstWhere((e) => e["symbol"] == selected,
          orElse: () => {"weight_percent": 0});

      setState(() {
        userSelectedElement = selected;
        controller1.text = fe["weight_percent"].toString();
        controller2.text = x["weight_percent"].toString();
      });
    }
  }

  @override
  void dispose() {
    controller1.dispose();
    controller2.dispose();
    tempMinController.dispose(); // EKLE
    tempMaxController.dispose(); // EKLE
    // Element controller'larını da temizle
    for (var controller in elementControllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    if (widget.source == 'binary_phase') {
      tempController.text = '1000.0';
      showConditionInputs = false;
    }
    controller1.text = '100';
    controller2.text = '0';

    controller1.addListener(() {
      final value = int.tryParse(controller1.text);
      if (value != null && value <= 100) {
        controller2.text = (100 - value).toString();
      }
    });

    controller2.addListener(() {
      final value = int.tryParse(controller2.text);
      if (value != null && value <= 100) {
        controller1.text = (100 - value).toString();
      }
    });

    loadElements();
  }

  Future<void> loadElements() async {
    final jsonString =
        await rootBundle.loadString('assets/data/periodic_table.json');
    final jsonMap = json.decode(jsonString);
    final List<dynamic> jsonList = jsonMap["elements"];

    setState(() {
      elements = jsonList.map((e) => ElementData.fromJson(e)).toList();
    });
  }

  // Element seçim fonksiyonu (çoklu element için)
  // Element seçim fonksiyonu (çoklu element için)
  // Element seçim fonksiyonu (çoklu element için)
  void _selectElement(String symbol) {
    if (symbol == 'FE') return; // FE sabit

    setState(() {
      // Eğer element zaten seçiliyse, çıkar
      if (selectedElements.any((elem) => elem['symbol'] == symbol)) {
        selectedElements.removeWhere((elem) => elem['symbol'] == symbol);
      } else {
        // Yeni element ekle
        if (selectedElements.length < 5) {
          selectedElements.add(
              {'symbol': symbol, 'weight_percent': 0.0, 'is_fixed': false});
        }
      }

      _updatePercentages();
      userSelectedElement = symbol;
    });
  }

  // Element yüzdesi düzenleme dialog'u
  void _editElementPercentage(int index) {
    final elem = selectedElements[index];
    final controller =
        TextEditingController(text: elem['weight_percent'].toStringAsFixed(1));

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('${elem['symbol']} Yüzdesi'),
        content: TextField(
          controller: controller,
          keyboardType: TextInputType.numberWithOptions(decimal: true),
          decoration: InputDecoration(
            labelText: 'Yüzde',
            suffixText: '%',
            border: OutlineInputBorder(),
          ),
          autofocus: true,
          onTap: () {
            // Metni seç
            controller.selection = TextSelection(
              baseOffset: 0,
              extentOffset: controller.text.length,
            );
          },
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('İptal'),
          ),
          TextButton(
            onPressed: () {
              final newValue = double.tryParse(controller.text);
              if (newValue != null && newValue >= 0 && newValue <= 100) {
                setState(() {
                  elem['weight_percent'] = newValue;

                  // FE'yi otomatik hesapla
                  double otherElementsTotal = 0.0;
                  for (var element in selectedElements) {
                    if (element['symbol'] != 'FE') {
                      otherElementsTotal += element['weight_percent'];
                    }
                  }

                  final feElement =
                      selectedElements.firstWhere((e) => e['symbol'] == 'FE');
                  double fePercent = 100.0 - otherElementsTotal;
                  if (fePercent < 0) fePercent = 0.0;
                  feElement['weight_percent'] = fePercent;
                });
                Navigator.pop(context);
              }
            },
            child: Text('Tamam'),
          ),
        ],
      ),
    );
  }

  void _redistributePercentages() {
    final nonFeElements =
        selectedElements.where((e) => e['symbol'] != 'FE').toList();

    if (nonFeElements.isNotEmpty) {
      // Her element için eşit pay (FE hariç)
      final equalPercent =
          90.0 / nonFeElements.length; // %90'ı böl, %10 FE'ye bırak

      for (var elem in nonFeElements) {
        elem['weight_percent'] = equalPercent;

        // Controller oluştur veya güncelle
        if (!elementControllers.containsKey(elem['symbol'])) {
          elementControllers[elem['symbol']] = TextEditingController();
        }
        elementControllers[elem['symbol']]!.text =
            equalPercent.toStringAsFixed(2);
      }

      // FE'yi hesapla
      final feElement = selectedElements.firstWhere((e) => e['symbol'] == 'FE');
      feElement['weight_percent'] =
          100.0 - (equalPercent * nonFeElements.length);

      // FE controller'ını güncelle
      if (elementControllers.containsKey('FE')) {
        elementControllers['FE']!.text =
            feElement['weight_percent'].toStringAsFixed(2);
      }
    }
  }

  void _updatePercentages() {
    final nonFeElements =
        selectedElements.where((e) => e['symbol'] != 'FE').toList();
    if (nonFeElements.isNotEmpty) {
      final availablePercent = 95.0; // FE için %5 bırak
      final perElement = availablePercent / nonFeElements.length;

      for (var elem in nonFeElements) {
        elem['weight_percent'] = perElement;
      }

      // FE yüzdesini güncelle
      final feElement = selectedElements.firstWhere((e) => e['symbol'] == 'FE');
      feElement['weight_percent'] = 100.0 - (perElement * nonFeElements.length);
    }
  }

  // Çoklu element hesaplama fonksiyonu
// Çoklu element hesaplama fonksiyonu
  Future<void> _performMultiElementCalculation() async {
    // Element validasyonu
    final totalPercent =
        selectedElements.fold(0.0, (sum, elem) => sum + elem['weight_percent']);
    if ((totalPercent - 100.0).abs() > 0.01) {
      setState(() {
        _errorMessage =
            'Toplam yüzde 100 olmalı. Şu an: ${totalPercent.toStringAsFixed(2)}%';
        _isLoading = false;
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final response = await http.post(
        Uri.parse(_multiElementUrl),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'elements': selectedElements
              .map((elem) => {
                    'symbol': elem['symbol'],
                    'weight_percent': elem['weight_percent']
                  })
              .toList(),
          'temperature_c': double.tryParse(tempController.text) ?? 1000.0,
          'pressure_pa': double.tryParse(pressureController.text) ?? 100000.0,
        }),
      );

      setState(() => _isLoading = false);

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);

        // Backend'den gelen veriyi düzgün şekilde işle
        widget.onCalculationComplete({
          'result': {
            'success': data['success'],
            'message': data['message'],
            'basic_properties': data['basic_properties'],
            'phase_data': data['phase_data'],
            'stable_phases': data['stable_phases'],
            'additional_properties': data['additional_properties'],
            'component_amounts': data['component_amounts'],
            'u_fraction_data': data['u_fraction_data'],
            'mu_elements': data['mu_elements'],
          },
          'elements': selectedElements,
          'temperature': double.tryParse(tempController.text) ?? 1000.0,
          'composition_type': 'multi_element',
        });
      } else {
        final Map<String, dynamic> errorData = json.decode(response.body);
        setState(() {
          _errorMessage =
              errorData['detail'] ?? 'Çoklu element hesaplama hatası.';
        });
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
        _errorMessage = 'Sunucuya bağlanılamadı: ${e.toString()}';
      });
    }
  }

  // FE yüzdesini güncelleyen yardımcı fonksiyon
  void _updateFePercentage() {
    double otherElementsTotal = 0.0;
    for (var element in selectedElements) {
      if (element['symbol'] != 'FE') {
        otherElementsTotal += element['weight_percent'];
      }
    }

    final feElement = selectedElements.firstWhere((e) => e['symbol'] == 'FE');
    double fePercent = 100.0 - otherElementsTotal;

    if (fePercent < 0) {
      fePercent = 0.0;
    }

    feElement['weight_percent'] = fePercent;
  }

  // Hesaplama işlemini gerçekleştiren fonksiyon
  Future<void> _performCalculation() async {
    if (widget.source == 'single_point') {
      if (selectedElements.length < 2) {
        setState(() {
          _errorMessage = 'Lütfen Fe dışında en az bir element seçin.';
        });
        return;
      }

      setState(() {
        _isLoading = true;
        _errorMessage = null;
      });

      try {
        // Flutter tarafında backend formatına uygun veri hazırla
        final elementSymbols =
            selectedElements.map((e) => e['symbol'] as String).toList();
        final weightPercents = {
          for (var e in selectedElements) e['symbol']: e['weight_percent']
        };

        final response = await http.post(
          Uri.parse(_singlePointUrl),
          headers: {'Content-Type': 'application/json; charset=utf-8'},
          body: json.encode({
            'elements': elementSymbols,
            'weight_percents': weightPercents,
            'temperature_c': double.tryParse(tempController.text) ?? 1000.0,
            'pressure_pa': double.tryParse(pressureController.text) ?? 100000.0,
          }),
        );

        setState(() => _isLoading = false);

        if (response.statusCode == 200) {
          final Map<String, dynamic> data =
              json.decode(utf8.decode(response.bodyBytes));

          widget.onCalculationComplete({
            'result': {
              'success': data['success'],
              'message': data['message'],
              'basic_properties': data['basic_properties'],
              'phase_data': data['phase_data'],
              'stable_phases': data['stable_phases'],
              'additional_properties': data['additional_properties'],
              'session_id': data['session_id'],
            },
            'elements': selectedElements,
            'temperature': double.tryParse(tempController.text) ?? 1000.0,
            'composition_type': 'single_point',
          });
        } else {
          final Map<String, dynamic> errorData = json.decode(response.body);
          setState(() {
            _errorMessage =
                errorData['detail'] ?? 'Single point hesaplama hatası.';
          });
        }
      } catch (e) {
        setState(() {
          _isLoading = false;
          _errorMessage = 'Sunucuya bağlanılamadı: ${e.toString()}';
        });
      }
    } else if (widget.source == 'binary_phase') {
      if (userSelectedElement == null) return;

      setState(() {
        _isLoading = true;
        _errorMessage = null;
      });

      try {
        final response = await http.post(
          Uri.parse(_binaryUrl),
          headers: {'Content-Type': 'application/json'},
          body: json.encode({
            'element_x': userSelectedElement,
            'x_axis_type': selectedXAxisType,
            'y_axis_type': selectedYAxisType,
          }),
        );

        setState(() => _isLoading = false);

        if (response.statusCode == 200) {
          final Map<String, dynamic> data = json.decode(response.body);

          widget.onCalculationComplete({
            'result': data,
            'solute': userSelectedElement,
            'diagram_base64': data['diagram_base64'],
            'element_pair': data['element_pair'],
          });
        } else {
          final Map<String, dynamic> errorData = json.decode(response.body);
          setState(() {
            _errorMessage =
                errorData['detail'] ?? 'Binary diagram oluşturma hatası.';
          });
        }
      } catch (e) {
        setState(() {
          _isLoading = false;
          _errorMessage = 'Sunucuya bağlanılamadı: ${e.toString()}';
        });
      }
    } // _performCalculation() metoduna ternary case'i ekle (diğer else if blokları arasına)
    else if (widget.source == 'ternary') {
      if (selectedElements.length < 3) {
        setState(() {
          _errorMessage =
              'Ternary diagram için Fe dahil en az 3 element seçin.';
        });
        return;
      }

      setState(() {
        _isLoading = true;
        _errorMessage = null;
      });

      try {
        final nonFeElements =
            selectedElements.where((e) => e['symbol'] != 'FE').toList();

        final response = await http.post(
          Uri.parse('http://127.0.0.1:8000/ternary-diagram'),
          headers: {'Content-Type': 'application/json'},
          body: json.encode({
            'element1': nonFeElements[0]['symbol'],
            'element2': nonFeElements[1]['symbol'],
            'weight_percent1': nonFeElements[0]['weight_percent'],
            'weight_percent2': nonFeElements[1]['weight_percent'],
            'temperature_c': double.tryParse(tempController.text) ?? 1000.0,
            'pressure_pa': double.tryParse(pressureController.text) ?? 101325.0,
            'diagram_type': selectedTernaryType, // Seçilen tipi gönder
            // Vertical için ek parametreler
            if (selectedTernaryType == 'vertical') ...{
              'temp_min': double.tryParse(tempMinController.text) ?? 300.0,
              'temp_max': double.tryParse(tempMaxController.text) ?? 1800.0,
            }
          }),
        );

        setState(() => _isLoading = false);

        if (response.statusCode == 200) {
          final Map<String, dynamic> data = json.decode(response.body);
          widget.onCalculationComplete({
            'result': data,
            'elements': selectedElements, // Bu önemli
            'temperature':
                double.tryParse(tempController.text) ?? 1000.0, // Bu da
            'composition_type': 'ternary',
          });
        } else {
          final Map<String, dynamic> errorData = json.decode(response.body);
          setState(() {
            _errorMessage =
                errorData['detail'] ?? 'Ternary diagram oluşturma hatası.';
          });
        }
      } catch (e) {
        setState(() {
          _isLoading = false;
          _errorMessage = 'Sunucuya bağlanılamadı: ${e.toString()}';
        });
      }
    }
  }

  // FE'yi diğer elementlere göre güncelle
  void _updateFeFromOtherElements() {
    double otherElementsTotal = 0.0;

    // FE dışındaki elementlerin toplamını hesapla
    for (var element in selectedElements) {
      if (element['symbol'] != 'FE') {
        otherElementsTotal += element['weight_percent'];
      }
    }

    // FE'yi hesapla
    final feElement = selectedElements.firstWhere((e) => e['symbol'] == 'FE');
    double fePercent = 100.0 - otherElementsTotal;

    if (fePercent < 0) fePercent = 0.0;
    if (fePercent > 100) fePercent = 100.0;

    feElement['weight_percent'] = fePercent;

    // FE controller'ını güncelle
    if (elementControllers.containsKey('FE')) {
      elementControllers['FE']!.text = fePercent.toStringAsFixed(2);
    }
  }

  // Yüzde düzenleme dialog'u
  void _editPercentage(int index) {
    final elem = selectedElements[index];
    final controller =
        TextEditingController(text: elem['weight_percent'].toStringAsFixed(2));

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('${elem['symbol']} Yüzdesi'),
        content: TextField(
          controller: controller,
          keyboardType: TextInputType.numberWithOptions(decimal: true),
          decoration: InputDecoration(
            labelText: 'Yüzde',
            suffixText: '%',
            border: OutlineInputBorder(),
          ),
          autofocus: true,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('İptal'),
          ),
          TextButton(
            onPressed: () {
              final newValue = double.tryParse(controller.text);
              if (newValue != null && newValue >= 0 && newValue <= 100) {
                setState(() {
                  elem['weight_percent'] = newValue;
                  _updateFePercentage();
                });
                Navigator.pop(context);
              }
            },
            child: Text('Tamam'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    const int maxColumns = 18;
    const double cellSize = 32;

    return Column(
      children: [
        // Hata mesajı gösterimi
        if (_errorMessage != null)
          Container(
            padding: const EdgeInsets.all(12),
            margin: const EdgeInsets.only(bottom: 16),
            decoration: BoxDecoration(
              color: Colors.red.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.red.shade300),
            ),
            child: Text(
              _errorMessage!,
              style: TextStyle(
                  color: Colors.red.shade700, fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
          ),

        Expanded(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Sol Panel
              Expanded(
                flex: 3,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    ToggleButtons(
                      isSelected: [true, false],
                      onPressed: (_) {},
                      borderRadius: BorderRadius.circular(4),
                      children: [
                        Padding(
                          padding: EdgeInsets.symmetric(horizontal: 12),
                          child: Text("Periodic Table"),
                        ),
                        Padding(
                          padding: EdgeInsets.symmetric(horizontal: 12),
                          child: Text("Alphabetic List"),
                        ),
                      ],
                    ),
                    SizedBox(height: 8),
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: SizedBox(
                        width: cellSize * maxColumns,
                        height: cellSize * 10.5,
                        child: elements.isEmpty
                            ? Center(child: CircularProgressIndicator())
                            : Stack(
                                children: elements
                                    .map((e) => _buildElementBox(e, cellSize))
                                    .toList(),
                              ),
                      ),
                    ),
                    SizedBox(height: 8),

                    // Single point için kompozisyon paneli
                    if (widget.source == 'single_point' ||
                        widget.source == 'ternary' &&
                            showCompositionInputs) ...[
                      Divider(thickness: 1),
                    ],

                    if (showConditionInputs ||
                        (widget.source == 'binary_phase' &&
                            showBinaryConfig)) ...[
                      Divider(thickness: 1),
                      // Ekran yüksekliğine göre dinamik alan
                      Flexible(
                        child: SingleChildScrollView(
                          padding: const EdgeInsets.all(8.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              if (widget.source == 'binary_phase') ...[
                                Text("Binary Phase Diagram Settings",
                                    style:
                                        TextStyle(fontWeight: FontWeight.bold)),
                                SizedBox(height: 12),
                                Text("X Axis Type:",
                                    style:
                                        TextStyle(fontWeight: FontWeight.bold)),
                                DropdownButton<String>(
                                  value: selectedXAxisType,
                                  isExpanded: true,
                                  items: [
                                    DropdownMenuItem(
                                        value: "mol",
                                        child: Text("Mol Fraksiyonu")),
                                    DropdownMenuItem(
                                        value: "wt",
                                        child: Text("Ağırlıkça %")),
                                  ],
                                  onChanged: (value) {
                                    setState(() {
                                      selectedXAxisType = value!;
                                    });
                                  },
                                ),
                                SizedBox(height: 12),
                                Text("Y Axis Type:",
                                    style:
                                        TextStyle(fontWeight: FontWeight.bold)),
                                DropdownButton<String>(
                                  value: selectedYAxisType,
                                  isExpanded: true,
                                  items: [
                                    DropdownMenuItem(
                                        value: "kelvin", child: Text("Kelvin")),
                                    DropdownMenuItem(
                                        value: "celsius",
                                        child: Text("Celsius")),
                                  ],
                                  onChanged: (value) {
                                    setState(() {
                                      selectedYAxisType = value!;
                                    });
                                  },
                                ),
                              ] else if (widget.source == 'single_point' ||
                                  widget.source == 'ternary') ...[
                                Text("Hesaplama Koşulları",
                                    style:
                                        TextStyle(fontWeight: FontWeight.bold)),
                                SizedBox(height: 12),
                                _buildConditionInput(
                                    "Sıcaklık (°C)", tempController),
                                _buildConditionInput(
                                    "Basınç (Pa)", pressureController),
                              ],
                              SizedBox(height: 12),
                              ElevatedButton(
                                onPressed:
                                    _isLoading ? null : _performCalculation,
                                child: _isLoading
                                    ? SizedBox(
                                        width: 20,
                                        height: 20,
                                        child: CircularProgressIndicator(),
                                      )
                                    : Text("Calculate"),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ]
                  ],
                ),
              ),

              SizedBox(width: 16),

              // Sağ Panel
              Container(
                width: 240,
                padding: EdgeInsets.all(12),
                decoration: BoxDecoration(
                  border: Border(left: BorderSide(color: Colors.grey.shade300)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text("Material",
                        style: TextStyle(fontWeight: FontWeight.bold)),
                    SizedBox(height: 8),
                    Text("Material name:"),
                    TextField(),
                    SizedBox(height: 16),

                    // Binary phase için UI
                    if (widget.source == 'binary_phase') ...[
                      Text("Binary Phase Diagram",
                          style: TextStyle(fontWeight: FontWeight.bold)),
                      SizedBox(height: 8),
                      if (userSelectedElement != null) ...[
                        Text("Selected: Fe-${userSelectedElement}"),
                        SizedBox(height: 16),
                        ElevatedButton(
                          onPressed: !_isLoading
                              ? () {
                                  setState(() {
                                    showBinaryConfig = true;
                                  });
                                }
                              : null,
                          child: Text("Configure Diagram"),
                        ),
                      ] else ...[
                        Text(
                            "Please select an element from the periodic table"),
                      ],
                    ] else if (widget.source == 'single_point') ...[
                      Text("Multi-Element Calculation",
                          style: TextStyle(fontWeight: FontWeight.bold)),
                      SizedBox(height: 8),
                      Text("Seçili Elementler: ${selectedElements.length}"),
                      SizedBox(height: 8),
                      Container(
                        constraints: BoxConstraints(maxHeight: 150),
                        child: ListView.builder(
                          shrinkWrap: true,
                          itemCount: selectedElements.length,
                          itemBuilder: (context, index) {
                            final elem = selectedElements[index];
                            return Padding(
                              padding: const EdgeInsets.only(bottom: 7.0),
                              child: Row(
                                children: [
                                  SizedBox(
                                    width: 30,
                                    child: Text(
                                      elem['symbol'],
                                      style: TextStyle(
                                          fontWeight: FontWeight.bold,
                                          fontSize: 14),
                                    ),
                                  ),
                                  Expanded(
                                    child: GestureDetector(
                                      onTap: () =>
                                          _editElementPercentage(index),
                                      child: Container(
                                        padding: EdgeInsets.symmetric(
                                            vertical: 8, horizontal: 6),
                                        decoration: BoxDecoration(
                                          border: Border.all(
                                              color: Colors.grey.shade400),
                                          borderRadius:
                                              BorderRadius.circular(4),
                                        ),
                                        child: Row(
                                          mainAxisAlignment:
                                              MainAxisAlignment.spaceBetween,
                                          children: [
                                            Text(
                                              elem['weight_percent']
                                                  .toStringAsFixed(1),
                                              style: TextStyle(fontSize: 14),
                                            ),
                                            Text('%',
                                                style: TextStyle(
                                                    color:
                                                        Colors.grey.shade600)),
                                          ],
                                        ),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            );
                          },
                        ),
                      ),
                      SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: () {
                          setState(() {
                            showConditionInputs = true;
                          });
                        },
                        child: Text("Set Conditions"),
                      ),
                    ] else if (widget.source == 'ternary') ...[
                      Text("Ternary Phase Diagram",
                          style: TextStyle(fontWeight: FontWeight.bold)),
                      SizedBox(height: 8),
                      Text("Seçili Elementler: ${selectedElements.length}"),
                      SizedBox(height: 8),

                      // Seçili elementleri göster
                      Container(
                        constraints: BoxConstraints(maxHeight: 120),
                        child: ListView.builder(
                          shrinkWrap: true,
                          itemCount: selectedElements.length,
                          itemBuilder: (context, index) {
                            final elem = selectedElements[index];
                            return Padding(
                              padding: const EdgeInsets.only(bottom: 4.0),
                              child: Row(
                                children: [
                                  SizedBox(
                                    width: 25,
                                    child: Text(
                                      elem['symbol'],
                                      style: TextStyle(
                                          fontWeight: FontWeight.bold,
                                          fontSize: 12),
                                    ),
                                  ),
                                  Expanded(
                                    child: GestureDetector(
                                      // EKLE
                                      onTap: () =>
                                          _editElementPercentage(index), // EKLE
                                      child: Container(
                                        // EKLE
                                        padding: EdgeInsets.symmetric(
                                            vertical: 8, horizontal: 6), // EKLE
                                        decoration: BoxDecoration(
                                          // EKLE
                                          border: Border.all(
                                              color:
                                                  Colors.grey.shade400), // EKLE
                                          borderRadius:
                                              BorderRadius.circular(4), // EKLE
                                        ), // EKLE
                                        child: Row(
                                          // EKLE
                                          mainAxisAlignment: MainAxisAlignment
                                              .spaceBetween, // EKLE
                                          children: [
                                            // EKLE
                                            Text(
                                              elem['weight_percent']
                                                  .toStringAsFixed(1),
                                              style: TextStyle(fontSize: 12),
                                            ),
                                            Text('%',
                                                style: TextStyle(
                                                    color: Colors.grey
                                                        .shade600)), // EKLE
                                          ], // EKLE
                                        ), // EKLE
                                      ), // EKLE
                                    ), // EKLE
                                  ),
                                ],
                              ),
                            );
                          },
                        ),
                      ),
                      SizedBox(height: 16),

                      if (selectedElements.length >= 3) ...[
                        Text("Diagram Type:",
                            style: TextStyle(fontWeight: FontWeight.bold)),
                        SizedBox(height: 8),

                        Column(
                          children: [
                            RadioListTile<String>(
                              title: Text("Isothermal",
                                  style: TextStyle(fontSize: 12)),
                              value: "isothermal",
                              groupValue:
                                  selectedTernaryType, // Yeni state değişkeni
                              onChanged: (value) {
                                setState(() {
                                  selectedTernaryType = value!;
                                });
                              },
                              dense: true,
                              contentPadding: EdgeInsets.zero,
                            ),
                            RadioListTile<String>(
                              title: Text("Vertical Section",
                                  style: TextStyle(fontSize: 12)),
                              value: "vertical",
                              groupValue: selectedTernaryType,
                              onChanged: (value) {
                                setState(() {
                                  selectedTernaryType = value!;
                                });
                              },
                              dense: true,
                              contentPadding: EdgeInsets.zero,
                            ),
                          ],
                        ),

                        // Vertical seçiliyse sıcaklık aralığı
                        if (selectedTernaryType == 'vertical') ...[
                          SizedBox(height: 8),
                          Text("Sıcaklık Aralığı:",
                              style: TextStyle(
                                  fontWeight: FontWeight.bold, fontSize: 11)),
                          SizedBox(height: 4),
                          Row(
                            children: [
                              Expanded(
                                child: TextField(
                                  controller: tempMinController,
                                  decoration: InputDecoration(
                                    labelText: 'Min (°C)',
                                    isDense: true,
                                    border: OutlineInputBorder(),
                                  ),
                                  style: TextStyle(fontSize: 10),
                                  keyboardType: TextInputType.number,
                                ),
                              ),
                              SizedBox(width: 4),
                              Expanded(
                                child: TextField(
                                  controller: tempMaxController,
                                  decoration: InputDecoration(
                                    labelText: 'Max (°C)',
                                    isDense: true,
                                    border: OutlineInputBorder(),
                                  ),
                                  style: TextStyle(fontSize: 10),
                                  keyboardType: TextInputType.number,
                                ),
                              ),
                            ],
                          ),
                        ],

                        SizedBox(height: 16),
                        ElevatedButton(
                          onPressed: () {
                            setState(() {
                              showConditionInputs = true;
                            });
                          },
                          child: Text("Set Conditions"),
                        ),
                      ] else ...[
                        Text("Fe dahil en az 3 element seçin",
                            style:
                                TextStyle(color: Colors.orange, fontSize: 12)),
                      ],
                    ],

                    Spacer(),
                    ElevatedButton(
                      onPressed: () {},
                      child: Text("Load Material"),
                    ),
                    SizedBox(height: 6),
                    ElevatedButton(
                      onPressed: () {},
                      child: Text("Save Material As..."),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

// Element yüzdesi düzenleme dialog'u

  Widget _buildConditionInput(String label, TextEditingController controller,
      {String? unit}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Expanded(flex: 2, child: Text(label)),
          Expanded(
            flex: 2,
            child: TextField(
              controller: controller,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(isDense: true),
            ),
          ),
          if (unit != null) ...[
            SizedBox(width: 8),
            SizedBox(
              width: 10,
              child: Text(unit),
            ),
          ]
        ],
      ),
    );
  }

  Widget _buildElementBox(ElementData element, double cellSize) {
    final symbol = element.symbol.toUpperCase();
    final isFixed = symbol == fixedElement;
    final isSelectable = selectableElements.contains(symbol);
    final isSelected = selectedElements.any((elem) => elem['symbol'] == symbol);

    Color bgColor;
    if (isFixed) {
      bgColor = Colors.red.shade300;
    } else if (isSelected) {
      bgColor = Colors.orange.shade400;
    } else if (isSelectable) {
      bgColor = Colors.blue.shade100;
    } else {
      bgColor = Colors.grey.shade300;
    }

    return Positioned(
      left: (element.group - 1) * cellSize,
      top: (element.period - 1) * cellSize,
      child: GestureDetector(
        onTap: isSelectable && widget.source == 'single_point'
            ? () => _selectElement(symbol)
            : isSelectable && widget.source == 'ternary' // YENİ
                ? () => _selectElement(symbol) // YENİ
                : isSelectable && widget.source == 'binary_phase'
                    ? () {
                        setState(() {
                          userSelectedElement = symbol;
                        });
                      }
                    : null,
        child: Container(
          width: cellSize,
          height: cellSize,
          decoration: BoxDecoration(
            color: bgColor,
            border: Border.all(color: Colors.black26),
            borderRadius: BorderRadius.circular(4),
          ),
          child: Center(
            child: Text(
              element.symbol,
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 11,
                color: isSelectable || isFixed
                    ? Colors.black
                    : Colors.grey.shade600,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class ElementData {
  final String symbol;
  final String name;
  final int number;
  final String category;
  final String summary;
  final int group;
  final int period;

  ElementData({
    required this.symbol,
    required this.name,
    required this.number,
    required this.category,
    required this.summary,
    required this.group,
    required this.period,
  });

  factory ElementData.fromJson(Map<String, dynamic> json) {
    return ElementData(
      symbol: json["symbol"] ?? "",
      name: json["name"] ?? "",
      number: json["number"] ?? 0,
      category: json["category"] ?? "",
      summary: json["summary"] ?? "",
      group: json["xpos"] ?? 1,
      period: json["ypos"] ?? 1,
    );
  }
}

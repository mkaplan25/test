import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;

class SinglePointDisplay extends StatefulWidget {
  final Map<String, dynamic> result;
  final String solute;
  final double temperature;
  final double weightPercent;
  final String? sessionId;
  final List<Map<String, dynamic>>? elements;

  const SinglePointDisplay({
    Key? key,
    required this.result,
    required this.solute,
    required this.temperature,
    required this.weightPercent,
    this.sessionId,
    this.elements,
  }) : super(key: key);

  @override
  State<SinglePointDisplay> createState() => _SinglePointDisplayState();
}

class _SinglePointDisplayState extends State<SinglePointDisplay>
    with TickerProviderStateMixin {
  late TabController _tabController;
  final ScrollController _scrollController = ScrollController();

  final List<String> _tabs = ['Özet', 'Fazlar', 'Analiz'];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _tabs.length, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bool success = widget.result['success'] ?? false;
    final String message = widget.result['message'] ?? '';

    return Container(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          _buildHeader(),

          SizedBox(height: 16),

          // Status message
          if (message.isNotEmpty) _buildStatusMessage(success, message),

          SizedBox(height: 16),

          // Tab bar
          Container(
            decoration: BoxDecoration(
              color: Colors.grey.shade100,
              borderRadius: BorderRadius.circular(8),
            ),
            child: TabBar(
              controller: _tabController,
              indicatorColor: Colors.blue.shade600,
              labelColor: Colors.blue.shade800,
              unselectedLabelColor: Colors.grey.shade600,
              indicatorSize: TabBarIndicatorSize.tab,
              tabs: _tabs.map((tab) => Tab(text: tab)).toList(),
            ),
          ),

          SizedBox(height: 16),

          // Tab content
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildSummaryTab(),
                _buildPhasesTab(),
                SinglePointAnalysisPanel(sessionId: widget.sessionId),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.blue.shade600, Colors.blue.shade800],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(Icons.science, color: Colors.white, size: 32),
          SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Fe-${widget.solute} Sistemi',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                SizedBox(height: 4),
                Text(
                  '${widget.temperature.toStringAsFixed(1)}°C • ${widget.weightPercent.toStringAsFixed(2)}% ${widget.solute}',
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.9),
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          ),
          IconButton(
            onPressed: () => _exportResults(),
            icon: Icon(Icons.download, color: Colors.white),
            tooltip: 'Sonuçları Dışa Aktar',
          ),
        ],
      ),
    );
  }

  Widget _buildStatusMessage(bool success, String message) {
    return Container(
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: success ? Colors.green.shade50 : Colors.red.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: success ? Colors.green.shade300 : Colors.red.shade300,
        ),
      ),
      child: Row(
        children: [
          Icon(
            success ? Icons.check_circle : Icons.error,
            color: success ? Colors.green.shade600 : Colors.red.shade600,
            size: 20,
          ),
          SizedBox(width: 8),
          Expanded(
            child: Text(
              message,
              style: TextStyle(
                color: success ? Colors.green.shade700 : Colors.red.shade700,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryTab() {
    final basicProps =
        widget.result['basic_properties'] as Map<String, dynamic>?;
    final phaseData = widget.result['phase_data'] as List?;

    return SingleChildScrollView(
      controller: _scrollController,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle('Temel Özellikler'),
          if (basicProps != null) _buildBasicPropertiesCard(basicProps),
          SizedBox(height: 16),
          _buildSectionTitle('Kararlı Fazlar'),
          if (phaseData != null) _buildPhaseSummaryCard(phaseData),
        ],
      ),
    );
  }

  Widget _buildPhasesTab() {
    final phaseData = widget.result['phase_data'] as List?;
    final stablePhases = widget.result['stable_phases'] as List?;

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (stablePhases != null) ...[
            _buildSectionTitle('Kararlı Fazlar (${stablePhases.length})'),
            SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: stablePhases
                  .map((phase) => _buildPhaseChip(phase.toString()))
                  .toList(),
            ),
            SizedBox(height: 16),
          ],
          if (phaseData != null) ...[
            _buildSectionTitle('Faz Detayları'),
            SizedBox(height: 8),
            ...phaseData.map((phase) =>
                _buildPhaseDetailCard(phase as Map<String, dynamic>)),
          ],
        ],
      ),
    );
  }

  Widget _buildPropertiesTab() {
    final additionalProps =
        widget.result['additional_properties'] as Map<String, dynamic>?;

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (additionalProps != null) ...[
            if (additionalProps.containsKey('electrical'))
              _buildElectricalPropertiesCard(additionalProps['electrical']),
            SizedBox(height: 16),
            if (additionalProps.containsKey('thermal'))
              _buildThermalPropertiesCard(additionalProps['thermal']),
            SizedBox(height: 16),
            if (additionalProps.containsKey('elastic'))
              _buildMechanicalPropertiesCard(additionalProps['elastic']),
          ] else
            Center(
              child: Text(
                'Ek özellik verileri mevcut değil',
                style: TextStyle(color: Colors.grey.shade600),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildTablesTab() {
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle('Hesaplama Parametreleri'),
          _buildParametersTable(),
          SizedBox(height: 16),
          _buildSectionTitle('Kompozisyon Tablosu'),
          _buildCompositionTable(),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 8),
      child: Text(
        title,
        style: TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.bold,
          color: Colors.grey.shade800,
        ),
      ),
    );
  }

  Widget _buildBasicPropertiesCard(Map<String, dynamic> props) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            _buildPropertyRow('Gibbs Enerjisi',
                '${props['G']?.toStringAsFixed(2) ?? 'N/A'} J/mol'),
            _buildPropertyRow(
                'Entalpi', '${props['H']?.toStringAsFixed(2) ?? 'N/A'} J/mol'),
            _buildPropertyRow('Entropi',
                '${props['S']?.toStringAsFixed(4) ?? 'N/A'} J/mol·K'),
            _buildPropertyRow('Isıl Kapasite',
                '${props['Cp']?.toStringAsFixed(4) ?? 'N/A'} J/mol·K'),
            if (props['alloy_density'] != null)
              _buildPropertyRow('Yoğunluk',
                  '${props['alloy_density'].toStringAsFixed(4)} g/cm³'),
          ],
        ),
      ),
    );
  }

  Widget _buildPhaseSummaryCard(List phaseData) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: phaseData.map((phase) {
            final phaseMap = phase as Map<String, dynamic>;
            final phaseName = phaseMap['Faz'] ?? 'Bilinmeyen';
            final moles = phaseMap['Moles']?.toStringAsFixed(6) ?? 'N/A';
            final mass = phaseMap['Mass']?.toStringAsFixed(6) ?? 'N/A';

            return Container(
              margin: EdgeInsets.only(bottom: 8),
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.blue.shade200),
              ),
              child: Row(
                children: [
                  Expanded(
                    flex: 2,
                    child: Text(
                      phaseName,
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),
                  Expanded(child: Text('Mol: $moles')),
                  Expanded(child: Text('Kütle: $mass')),
                ],
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildQuickInfoGrid() {
    return GridView.count(
      shrinkWrap: true,
      physics: NeverScrollableScrollPhysics(),
      crossAxisCount: 2,
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
      childAspectRatio: 2.5,
      children: [
        _buildInfoCard('Sıcaklık', '${widget.temperature}°C', Icons.thermostat),
        _buildInfoCard('Kompozisyon',
            '${widget.weightPercent}% ${widget.solute}', Icons.pie_chart),
        _buildInfoCard('Sistem', 'Fe-${widget.solute}', Icons.category),
        _buildInfoCard('Basınç', '1 atm', Icons.compress),
      ],
    );
  }

  Widget _buildInfoCard(String title, String value, IconData icon) {
    return Card(
      elevation: 1,
      child: Padding(
        padding: EdgeInsets.all(12),
        child: Row(
          children: [
            Icon(icon, color: Colors.blue.shade600, size: 24),
            SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey.shade600,
                    ),
                  ),
                  Text(
                    value,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPhaseChip(String phaseName) {
    return Chip(
      label: Text(phaseName),
      backgroundColor: Colors.orange.shade100,
      labelStyle: TextStyle(
        color: Colors.orange.shade800,
        fontWeight: FontWeight.w500,
      ),
    );
  }

  Widget _buildPhaseDetailCard(Map<String, dynamic> phase) {
    return Card(
      margin: EdgeInsets.only(bottom: 12),
      child: ExpansionTile(
        title: Text(
          phase['Faz'] ?? 'Bilinmeyen Faz',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Text('Mol: ${phase['Moles']?.toStringAsFixed(6) ?? 'N/A'}'),
        children: [
          Padding(
            padding: EdgeInsets.all(16),
            child: Column(
              children: phase.entries
                  .where((entry) => entry.key != 'Faz')
                  .map((entry) => _buildPropertyRow(
                        entry.key,
                        entry.value?.toString() ?? 'N/A',
                      ))
                  .toList(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildElectricalPropertiesCard(Map<String, dynamic> electrical) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Elektriksel Özellikler',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 12),
            if (electrical['system_resistivity_micro_ohm_cm'] != null)
              _buildPropertyRow(
                'Özdirenç',
                '${electrical['system_resistivity_micro_ohm_cm'].toStringAsFixed(4)} μΩ·cm',
              ),
            if (electrical['electrical_conductivity_S_per_m'] != null)
              _buildPropertyRow(
                'İletkenlik',
                '${electrical['electrical_conductivity_S_per_m'].toStringAsFixed(2)} S/m',
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildThermalPropertiesCard(Map<String, dynamic> thermal) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Termal Özellikler',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 12),
            if (thermal['total_thermal_conductivity_W_per_mK'] != null)
              _buildPropertyRow(
                'Termal İletkenlik',
                '${thermal['total_thermal_conductivity_W_per_mK'].toStringAsFixed(4)} W/(m·K)',
              ),
            if (thermal['electronic_contribution_W_per_mK'] != null)
              _buildPropertyRow(
                'Elektronik Katkı',
                '${thermal['electronic_contribution_W_per_mK'].toStringAsFixed(4)} W/(m·K)',
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildMechanicalPropertiesCard(Map<String, dynamic> elastic) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Mekanik Özellikler',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 12),
            if (elastic['youngs_modulus_GPa'] != null)
              _buildPropertyRow(
                'Young Modülü',
                '${elastic['youngs_modulus_GPa'].toStringAsFixed(1)} GPa',
              ),
            if (elastic['shear_modulus_GPa'] != null)
              _buildPropertyRow(
                'Kayma Modülü',
                '${elastic['shear_modulus_GPa'].toStringAsFixed(1)} GPa',
              ),
            if (elastic['poisson_ratio'] != null)
              _buildPropertyRow(
                'Poisson Oranı',
                '${elastic['poisson_ratio'].toStringAsFixed(3)}',
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildParametersTable() {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Table(
          columnWidths: {
            0: FlexColumnWidth(2),
            1: FlexColumnWidth(3),
          },
          children: [
            _buildTableRow('Parametre', 'Değer', null, true),
            _buildTableRow('Element 1', 'Fe'),
            _buildTableRow('Element 2', widget.solute),
            _buildTableRow('Sıcaklık', '${widget.temperature}°C'),
            _buildTableRow(
                'Ağırlıkça %', '${widget.weightPercent}% ${widget.solute}'),
            _buildTableRow('Basınç', '1 atm'),
          ],
        ),
      ),
    );
  }

  Widget _buildCompositionTable() {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Table(
          columnWidths: {
            0: FlexColumnWidth(2),
            1: FlexColumnWidth(2),
            2: FlexColumnWidth(2),
          },
          children: [
            _buildTableRow('Element', 'Ağırlıkça %', 'Mol Fraksiyonu', true),
            _buildTableRow(
                'Fe',
                '${(100 - widget.weightPercent).toStringAsFixed(2)}%',
                'Hesaplanıyor...'),
            _buildTableRow(
                widget.solute,
                '${widget.weightPercent.toStringAsFixed(2)}%',
                'Hesaplanıyor...'),
          ],
        ),
      ),
    );
  }

  TableRow _buildTableRow(String col1, String col2,
      [String? col3, bool isHeader = false]) {
    final textStyle = TextStyle(
      fontWeight: isHeader ? FontWeight.bold : FontWeight.normal,
      color: isHeader ? Colors.grey.shade800 : Colors.grey.shade700,
    );

    return TableRow(
      decoration: isHeader ? BoxDecoration(color: Colors.grey.shade100) : null,
      children: [
        Padding(
          padding: EdgeInsets.all(8),
          child: Text(col1, style: textStyle),
        ),
        Padding(
          padding: EdgeInsets.all(8),
          child: Text(col2, style: textStyle),
        ),
        if (col3 != null)
          Padding(
            padding: EdgeInsets.all(8),
            child: Text(col3, style: textStyle),
          ),
      ],
    );
  }

  Widget _buildPropertyRow(String label, String value) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(
              color: Colors.grey.shade700,
              fontWeight: FontWeight.w500,
            ),
          ),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: Colors.grey.shade800,
            ),
          ),
        ],
      ),
    );
  }

  void _exportResults() {
    // Sonuçları clipboard'a kopyala
    final exportText = _generateExportText();
    Clipboard.setData(ClipboardData(text: exportText));

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Sonuçlar panoya kopyalandı'),
        backgroundColor: Colors.green,
      ),
    );
  }

  String _generateExportText() {
    final buffer = StringBuffer();
    buffer.writeln('Fe-${widget.solute} Sistemi Hesaplama Sonuçları');
    buffer.writeln('==========================================');
    buffer.writeln('Sıcaklık: ${widget.temperature}°C');
    buffer.writeln('Kompozisyon: ${widget.weightPercent}% ${widget.solute}');
    buffer.writeln('');

    final basicProps =
        widget.result['basic_properties'] as Map<String, dynamic>?;
    if (basicProps != null) {
      buffer.writeln('Temel Özellikler:');
      buffer.writeln(
          'Gibbs Enerjisi: ${basicProps['G']?.toStringAsFixed(2) ?? 'N/A'} J/mol');
      buffer.writeln(
          'Entalpi: ${basicProps['H']?.toStringAsFixed(2) ?? 'N/A'} J/mol');
      buffer.writeln(
          'Entropi: ${basicProps['S']?.toStringAsFixed(4) ?? 'N/A'} J/mol·K');
      buffer.writeln('');
    }

    return buffer.toString();
  }
}
// MultiElementDisplay widget'ı - single_point_display.dart dosyasının sonuna ekle

class MultiElementDisplay extends StatefulWidget {
  final Map<String, dynamic> result;
  final List<Map<String, dynamic>> elements;
  final double temperature;

  const MultiElementDisplay({
    Key? key,
    required this.result,
    required this.elements,
    required this.temperature,
  }) : super(key: key);

  @override
  State<MultiElementDisplay> createState() => _MultiElementDisplayState();
}

class _MultiElementDisplayState extends State<MultiElementDisplay>
    with TickerProviderStateMixin {
  late TabController _tabController;
  final ScrollController _scrollController = ScrollController();

  final List<String> _tabs = ['Özet', 'Fazlar', 'Özellikler', 'Tablolar'];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _tabs.length, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bool success = widget.result['success'] ?? false;
    final String message = widget.result['message'] ?? '';

    return Container(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildHeader(),
          SizedBox(height: 16),
          if (message.isNotEmpty) _buildStatusMessage(success, message),
          SizedBox(height: 16),
          Container(
            decoration: BoxDecoration(
              color: Colors.grey.shade100,
              borderRadius: BorderRadius.circular(8),
            ),
            child: TabBar(
              controller: _tabController,
              indicatorColor: Colors.blue.shade600,
              labelColor: Colors.blue.shade800,
              unselectedLabelColor: Colors.grey.shade600,
              indicatorSize: TabBarIndicatorSize.tab,
              tabs: _tabs.map((tab) => Tab(text: tab)).toList(),
            ),
          ),
          SizedBox(height: 16),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildSummaryTab(),
                _buildPhasesTab(),
                _buildPropertiesTab(),
                _buildTablesTab(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    final elementsList = widget.elements.map((e) => e['symbol']).join('-');
    final compositionText = widget.elements
        .map((e) => '${e['weight_percent'].toStringAsFixed(1)}% ${e['symbol']}')
        .join(', ');

    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.green.shade600, Colors.green.shade800],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(Icons.science, color: Colors.white, size: 32),
          SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Çoklu Element Sistemi ($elementsList)',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                SizedBox(height: 4),
                Text(
                  '${widget.temperature.toStringAsFixed(1)}°C • $compositionText',
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.9),
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
          IconButton(
            onPressed: () => _exportResults(),
            icon: Icon(Icons.download, color: Colors.white),
            tooltip: 'Sonuçları Dışa Aktar',
          ),
        ],
      ),
    );
  }

  Widget _buildStatusMessage(bool success, String message) {
    return Container(
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: success ? Colors.green.shade50 : Colors.red.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: success ? Colors.green.shade300 : Colors.red.shade300,
        ),
      ),
      child: Row(
        children: [
          Icon(
            success ? Icons.check_circle : Icons.error,
            color: success ? Colors.green.shade600 : Colors.red.shade600,
            size: 20,
          ),
          SizedBox(width: 8),
          Expanded(
            child: Text(
              message,
              style: TextStyle(
                color: success ? Colors.green.shade700 : Colors.red.shade700,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryTab() {
    final basicProps =
        widget.result['basic_properties'] as Map<String, dynamic>?;
    final phaseData = widget.result['phase_data'] as List?;

    return SingleChildScrollView(
      controller: _scrollController,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle('Element Kompozisyonu'),
          _buildCompositionCard(),
          SizedBox(height: 16),
          _buildSectionTitle('Temel Özellikler'),
          if (basicProps != null) _buildBasicPropertiesCard(basicProps),
          SizedBox(height: 16),
          _buildSectionTitle('Kararlı Fazlar'),
          if (phaseData != null) _buildPhaseSummaryCard(phaseData),
        ],
      ),
    );
  }

  Widget _buildCompositionCard() {
    return Card(
      elevation: 2,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Element Dağılımı',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 12),
            ...widget.elements.map((element) {
              return Container(
                margin: EdgeInsets.only(bottom: 8),
                padding: EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: element['is_fixed'] == true
                      ? Colors.red.shade50
                      : Colors.blue.shade50,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(
                    color: element['is_fixed'] == true
                        ? Colors.red.shade300
                        : Colors.blue.shade300,
                  ),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      element['symbol'],
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: element['is_fixed'] == true
                            ? Colors.red.shade700
                            : Colors.blue.shade700,
                      ),
                    ),
                    Text(
                      '${element['weight_percent'].toStringAsFixed(2)}%',
                      style: TextStyle(fontWeight: FontWeight.w500),
                    ),
                  ],
                ),
              );
            }).toList(),
          ],
        ),
      ),
    );
  }

  Widget _buildPhasesTab() {
    final phaseData = widget.result['phase_data'] as List?;
    final stablePhases = widget.result['stable_phases'] as List?;

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (stablePhases != null) ...[
            _buildSectionTitle('Kararlı Fazlar (${stablePhases.length})'),
            SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: stablePhases
                  .map((phase) => _buildPhaseChip(phase.toString()))
                  .toList(),
            ),
            SizedBox(height: 16),
          ],
          if (phaseData != null) ...[
            _buildSectionTitle('Faz Detayları'),
            SizedBox(height: 8),
            ...phaseData.map((phase) =>
                _buildPhaseDetailCard(phase as Map<String, dynamic>)),
          ],
        ],
      ),
    );
  }

  Widget _buildPropertiesTab() {
    final additionalProps =
        widget.result['additional_properties'] as Map<String, dynamic>?;

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (additionalProps != null) ...[
            if (additionalProps.containsKey('electrical'))
              _buildElectricalPropertiesCard(additionalProps['electrical']),
            SizedBox(height: 16),
            if (additionalProps.containsKey('thermal'))
              _buildThermalPropertiesCard(additionalProps['thermal']),
            SizedBox(height: 16),
            if (additionalProps.containsKey('elastic'))
              _buildMechanicalPropertiesCard(additionalProps['elastic']),
          ] else
            Center(
              child: Text(
                'Ek özellik verileri mevcut değil',
                style: TextStyle(color: Colors.grey.shade600),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildTablesTab() {
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle('Hesaplama Parametreleri'),
          _buildParametersTable(),
          SizedBox(height: 16),
          _buildSectionTitle('Kompozisyon Tablosu'),
          _buildMultiCompositionTable(),
        ],
      ),
    );
  }

  Widget _buildMultiCompositionTable() {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Table(
          columnWidths: {
            0: FlexColumnWidth(2),
            1: FlexColumnWidth(2),
            2: FlexColumnWidth(2),
          },
          children: [
            _buildTableRow('Element', 'Ağırlıkça %', 'Mol Fraksiyonu', true),
            ...widget.elements.map((elem) => _buildTableRow(
                  elem['symbol'],
                  '${elem['weight_percent'].toStringAsFixed(2)}%',
                  'Hesaplanıyor...',
                )),
          ],
        ),
      ),
    );
  }

  // SinglePointDisplay'deki helper metodları kopyala
  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 8),
      child: Text(
        title,
        style: TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.bold,
          color: Colors.grey.shade800,
        ),
      ),
    );
  }

  Widget _buildBasicPropertiesCard(Map<String, dynamic> props) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            _buildPropertyRow('Gibbs Enerjisi',
                '${props['G']?.toStringAsFixed(2) ?? 'N/A'} J/mol'),
            _buildPropertyRow(
                'Entalpi', '${props['H']?.toStringAsFixed(2) ?? 'N/A'} J/mol'),
            _buildPropertyRow('Entropi',
                '${props['S']?.toStringAsFixed(4) ?? 'N/A'} J/mol·K'),
            _buildPropertyRow('Isıl Kapasite',
                '${props['Cp']?.toStringAsFixed(4) ?? 'N/A'} J/mol·K'),
            if (props['alloy_density'] != null)
              _buildPropertyRow('Yoğunluk',
                  '${props['alloy_density'].toStringAsFixed(4)} g/cm³'),
          ],
        ),
      ),
    );
  }

  Widget _buildPhaseSummaryCard(List phaseData) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: phaseData.map((phase) {
            final phaseMap = phase as Map<String, dynamic>;
            final phaseName = phaseMap['Faz'] ?? 'Bilinmeyen';
            final moles = phaseMap['Moles']?.toStringAsFixed(6) ?? 'N/A';
            final mass = phaseMap['Mass']?.toStringAsFixed(6) ?? 'N/A';

            return Container(
              margin: EdgeInsets.only(bottom: 8),
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.green.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.green.shade200),
              ),
              child: Row(
                children: [
                  Expanded(
                    flex: 2,
                    child: Text(
                      phaseName,
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),
                  Expanded(child: Text('Mol: $moles')),
                  Expanded(child: Text('Kütle: $mass')),
                ],
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildPhaseChip(String phaseName) {
    return Chip(
      label: Text(phaseName),
      backgroundColor: Colors.green.shade100,
      labelStyle: TextStyle(
        color: Colors.green.shade800,
        fontWeight: FontWeight.w500,
      ),
    );
  }

  Widget _buildPhaseDetailCard(Map<String, dynamic> phase) {
    return Card(
      margin: EdgeInsets.only(bottom: 12),
      child: ExpansionTile(
        title: Text(
          phase['Faz'] ?? 'Bilinmeyen Faz',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Text('Mol: ${phase['Moles']?.toStringAsFixed(6) ?? 'N/A'}'),
        children: [
          Padding(
            padding: EdgeInsets.all(16),
            child: Column(
              children: phase.entries
                  .where((entry) => entry.key != 'Faz')
                  .map((entry) => _buildPropertyRow(
                        entry.key,
                        entry.value?.toString() ?? 'N/A',
                      ))
                  .toList(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildElectricalPropertiesCard(Map<String, dynamic> electrical) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Elektriksel Özellikler',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 12),
            if (electrical['system_resistivity_micro_ohm_cm'] != null)
              _buildPropertyRow(
                'Özdirenç',
                '${electrical['system_resistivity_micro_ohm_cm'].toStringAsFixed(4)} μΩ·cm',
              ),
            if (electrical['electrical_conductivity_S_per_m'] != null)
              _buildPropertyRow(
                'İletkenlik',
                '${electrical['electrical_conductivity_S_per_m'].toStringAsFixed(2)} S/m',
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildThermalPropertiesCard(Map<String, dynamic> thermal) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Termal Özellikler',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 12),
            if (thermal['total_thermal_conductivity_W_per_mK'] != null)
              _buildPropertyRow(
                'Termal İletkenlik',
                '${thermal['total_thermal_conductivity_W_per_mK'].toStringAsFixed(4)} W/(m·K)',
              ),
            if (thermal['electronic_contribution_W_per_mK'] != null)
              _buildPropertyRow(
                'Elektronik Katkı',
                '${thermal['electronic_contribution_W_per_mK'].toStringAsFixed(4)} W/(m·K)',
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildMechanicalPropertiesCard(Map<String, dynamic> elastic) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Mekanik Özellikler',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 12),
            if (elastic['youngs_modulus_GPa'] != null)
              _buildPropertyRow(
                'Young Modülü',
                '${elastic['youngs_modulus_GPa'].toStringAsFixed(1)} GPa',
              ),
            if (elastic['shear_modulus_GPa'] != null)
              _buildPropertyRow(
                'Kayma Modülü',
                '${elastic['shear_modulus_GPa'].toStringAsFixed(1)} GPa',
              ),
            if (elastic['poisson_ratio'] != null)
              _buildPropertyRow(
                'Poisson Oranı',
                '${elastic['poisson_ratio'].toStringAsFixed(3)}',
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildParametersTable() {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Table(
          columnWidths: {
            0: FlexColumnWidth(2),
            1: FlexColumnWidth(3),
          },
          children: [
            _buildTableRow('Parametre', 'Değer', null, true),
            _buildTableRow('Element Sayısı', '${widget.elements.length}'),
            _buildTableRow('Sıcaklık', '${widget.temperature}°C'),
            _buildTableRow('Basınç', '1 atm'),
            _buildTableRow('Hesaplama Tipi', 'Çoklu Element'),
          ],
        ),
      ),
    );
  }

  TableRow _buildTableRow(String col1, String col2,
      [String? col3, bool isHeader = false]) {
    final textStyle = TextStyle(
      fontWeight: isHeader ? FontWeight.bold : FontWeight.normal,
      color: isHeader ? Colors.grey.shade800 : Colors.grey.shade700,
    );

    return TableRow(
      decoration: isHeader ? BoxDecoration(color: Colors.grey.shade100) : null,
      children: [
        Padding(
          padding: EdgeInsets.all(8),
          child: Text(col1, style: textStyle),
        ),
        Padding(
          padding: EdgeInsets.all(8),
          child: Text(col2, style: textStyle),
        ),
        if (col3 != null)
          Padding(
            padding: EdgeInsets.all(8),
            child: Text(col3, style: textStyle),
          ),
      ],
    );
  }

  Widget _buildPropertyRow(String label, String value) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(
              color: Colors.grey.shade700,
              fontWeight: FontWeight.w500,
            ),
          ),
          Text(
            value,
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: Colors.grey.shade800,
            ),
          ),
        ],
      ),
    );
  }

  void _exportResults() {
    final exportText = _generateExportText();
    Clipboard.setData(ClipboardData(text: exportText));

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Sonuçlar panoya kopyalandı'),
        backgroundColor: Colors.green,
      ),
    );
  }

  String _generateExportText() {
    final buffer = StringBuffer();
    final elementsList = widget.elements.map((e) => e['symbol']).join('-');

    buffer.writeln('Çoklu Element Sistemi ($elementsList) Hesaplama Sonuçları');
    buffer.writeln('================================================');
    buffer.writeln('Sıcaklık: ${widget.temperature}°C');
    buffer.writeln('Element Kompozisyonu:');

    for (var element in widget.elements) {
      buffer.writeln(
          '  ${element['symbol']}: ${element['weight_percent'].toStringAsFixed(2)}%');
    }
    buffer.writeln('');

    final basicProps =
        widget.result['basic_properties'] as Map<String, dynamic>?;
    if (basicProps != null) {
      buffer.writeln('Temel Özellikler:');
      buffer.writeln(
          'Gibbs Enerjisi: ${basicProps['G']?.toStringAsFixed(2) ?? 'N/A'} J/mol');
      buffer.writeln(
          'Entalpi: ${basicProps['H']?.toStringAsFixed(2) ?? 'N/A'} J/mol');
      buffer.writeln(
          'Entropi: ${basicProps['S']?.toStringAsFixed(4) ?? 'N/A'} J/mol·K');
      buffer.writeln('');
    }

    return buffer.toString();
  }
}

class SinglePointAnalysisPanel extends StatefulWidget {
  final String? sessionId;
  const SinglePointAnalysisPanel({Key? key, required this.sessionId})
      : super(key: key);

  @override
  State<SinglePointAnalysisPanel> createState() =>
      _SinglePointAnalysisPanelState();
}

class _SinglePointAnalysisPanelState extends State<SinglePointAnalysisPanel> {
  bool _loading = false;
  dynamic _payload;
  String? _error;

  final List<String> _menuItems = const [
    "Density",
    "Density Phases",
    "Volume Data (System)",
    "Volume Data (Phase)",
    "Component Amounts",
    "Phase Weight Fractions",
    "Driving Forces",
    "u-Fractions",
    "Site Fractions (Thermo-Calc Style)",
    "Chemical Potentials",
    "Clean Phase-Ref Analysis",
    "Activities (System)",
    "Activities (Phase-Ref)",
    "Phase Properties",
    "Curie Temperature",
    "Bohr Magneton (with site fractions)",
    "Helmholtz",
    "System Gibbs Energy",
    "System Enthalpy",
    "System Entropy",
    "System Internal Energy",
    "System Heat Capacity",
    "Electrical Resistance",
    "Electrical Conductivity",
    "Thermal Conductivity",
    "Thermal Diffusivity",
    "Thermal Resistance",
    "Thermal Expansion",
    "Young's Modulus",
    "Shear Modulus",
    "Bulk Modulus",
    "Poisson Ratio",
    "Surface Tension Properties",
  ];

  Future<void> _runChoice(int index) async {
    if (widget.sessionId == null || widget.sessionId!.isEmpty) {
      setState(() => _error = "Session bulunamadı. Hesabı yeniden çalıştırın.");
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
      _payload = null;
    });

    try {
      final resp = await http.post(
        Uri.parse('http://127.0.0.1:8000/single-point-analysis'),
        headers: {
          'Content-Type': 'application/json; charset=utf-8'
        }, // ✅ charset eklendi
        body: json.encode({
          "session_id": widget.sessionId,
          "menu_choice": index + 1, // 1..N
        }),
      );

      if (resp.statusCode == 200) {
        final jsonResp =
            json.decode(utf8.decode(resp.bodyBytes)); // ✅ Türkçe karakter fix
        setState(() => _payload = jsonResp['payload']);
      } else {
        setState(() => _error =
            "Hata: ${utf8.decode(resp.bodyBytes)}"); // ✅ hata mesajı da fix
      }
    } catch (e) {
      setState(() => _error = "İstek hatası: $e");
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    // yatay bölünmüş panel
    return Row(
      children: [
        // Sol menü
        Expanded(
          flex: 2,
          child: Material(
            color: Colors.transparent,
            child: ListView.separated(
              itemCount: _menuItems.length,
              separatorBuilder: (_, __) => const Divider(height: 1),
              itemBuilder: (context, i) => Material(
                color: Colors.transparent,
                child: ListTile(
                  dense: true,
                  title: Text("${i + 1}. ${_menuItems[i]}",
                      style: const TextStyle(fontSize: 13)),
                  onTap: () => _runChoice(i),
                ),
              ),
            ),
          ),
        ),
        const VerticalDivider(width: 1),
        // Sağ sonuç
        Expanded(
          flex: 3,
          child: _loading
              ? const Center(child: CircularProgressIndicator())
              : _error != null
                  ? Padding(
                      padding: const EdgeInsets.all(12),
                      child: Text(_error!,
                          style: const TextStyle(color: Colors.red)),
                    )
                  : _payload == null
                      ? const Center(child: Text("Bir analiz seçin"))
                      : _buildPayloadView(_payload),
        ),
      ],
    );
  }

  Widget _buildPayloadView(dynamic payload) {
    if (payload is Map<String, dynamic>) {
      if (payload.length == 1 && payload.containsKey('text')) {
        return SingleChildScrollView(
          padding: const EdgeInsets.all(12),
          child: SelectableText(payload['text']?.toString() ?? ""),
        );
      }
      return SingleChildScrollView(
        padding: const EdgeInsets.all(12),
        child:
            SelectableText(const JsonEncoder.withIndent('  ').convert(payload)),
      );
    }
    return SingleChildScrollView(
      padding: const EdgeInsets.all(12),
      child: SelectableText(payload.toString()),
    );
  }
}

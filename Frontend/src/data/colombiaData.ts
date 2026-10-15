// ── Datos de Departamentos y Municipios de Colombia ─────────────
// Incluye los 32 departamentos + Bogotá D.C. y sus municipios principales.
// Organizado alfabéticamente con al menos 10 municipios por departamento,
// siendo el primero la capital departamental.

export const MUNICIPIOS_POR_DEPARTAMENTO: Record<string, string[]> = {
 'Amazonas': [
    'Leticia', 'El Encanto', 'La Chorrera', 'La Pedrera', 'La Victoria',
    'Mirití-Paraná', 'Puerto Alegría', 'Puerto Arica', 'Puerto Nariño', 'Puerto Santander', 'Tarapacá',
  ],
  'Antioquia': [
    'Medellín', 'Abejorral', 'Abriaquí', 'Alejandría', 'Amagá', 'Amalfi', 'Andes', 'Angelópolis',
    'Angostura', 'Anorí', 'Anzá', 'Apartadó', 'Arboletes', 'Argelia', 'Armenia', 'Barbosa',
    'Bello', 'Betania', 'Buriticá', 'Cáceres', 'Caldas', 'Envigado', 'Itagüí', 'Rionegro', 'Sabaneta',
  ],
  'Arauca': [
    'Arauca', 'Arauquita', 'Cravo Norte', 'Fortul', 'Puerto Rondón', 'Saravena', 'Tame',
    'Cubará', 'El Amparo', 'La Esmeralda',
  ],
  'Atlántico': [
    'Barranquilla', 'Baranoa', 'Campo de la Cruz', 'Candelaria', 'Galapa', 'Juan de Acosta',
    'Luruaco', 'Malambo', 'Manatí', 'Palmar de Varela', 'Piojó', 'Polonuevo', 'Ponedera',
    'Puerto Colombia', 'Repelón', 'Sabanagrande', 'Sabanalarga', 'Santa Lucía', 'Santo Tomás', 'Soledad',
  ],
  'Bogotá D.C.': [
    'Bogotá D.C.',
    'Usaquén', 'Chapinero', 'Santa Fe', 'San Cristóbal', 'Usme', 'Tunjuelito',
    'Bosa', 'Kennedy', 'Fontibón', 'Engativá', 'Suba', 'Barrios Unidos',
  ],
  'Bolívar': [
    'Cartagena', 'Achí', 'Altos del Rosario', 'Arenal', 'Arjona', 'Arroyohondo', 'Barranco de Loba',
    'Calamar', 'Cantagallo', 'Cicuco', 'Córdoba', 'El Carmen de Bolívar', 'El Guamo', 'El Peñón',
    'Hatillo de Loba', 'Magangué', 'Mahates', 'Margarita', 'Mompós', 'Montecristo', 'San Juan Nepomuceno',
  ],
  'Boyacá': [
    'Tunja', 'Aquitania', 'Arcabuco', 'Belén', 'Berbeo', 'Betéitiva', 'Boavita', 'Boyacá',
    'Briceño', 'Buena Vista', 'Caldas', 'Campohermoso', 'Cerinza', 'Chinavita', 'Chiquinquirá',
    'Chiscas', 'Chita', 'Chitaraque', 'Chivatá', 'Ciénega', 'Duitama', 'Garagoa', 'Paipa', 'Sogamoso', 'Villa de Leyva',
  ],
  'Caldas': [
    'Manizales', 'Aguadas', 'Anserma', 'Aranzazu', 'Belalcázar', 'Chinchiná', 'Filadelfia',
    'La Dorada', 'La Merced', 'Manzanares', 'Marmato', 'Marquetalia', 'Marulanda', 'Neira',
    'Norcasia', 'Pácora', 'Palestina', 'Pensilvania', 'Riosucio', 'Risaralda', 'Salamina', 'Samaná',
  ],
  'Caquetá': [
    'Florencia', 'Albania', 'Belén de Los Andaquíes', 'Cartagena del Chairá', 'Curillo', 'El Doncello',
    'El Paujil', 'La Montañita', 'Milán', 'Morelia', 'Puerto Rico', 'San José del Fragua',
    'San Vicente del Caguán', 'Solano', 'Solita', 'Valparaíso',
  ],
  'Casanare': [
    'Yopal', 'Aguazul', 'Chameza', 'Hato Corozal', 'La Salina', 'Maní', 'Monterrey',
    'Nunchía', 'Orocué', 'Paz de Ariporo', 'Pore', 'Recetor', 'Sabanalarga', 'Sácama',
    'San Luis de Palenque', 'Támara', 'Tauramena', 'Trinidad', 'Villanueva',
  ],
  'Cauca': [
    'Popayán', 'Almaguer', 'Argelia', 'Balboa', 'Bolívar', 'Buenos Aires', 'Cajibío',
    'Caldono', 'Caloto', 'Corinto', 'El Tambo', 'Florencia', 'Guachené', 'Guapi',
    'Inzá', 'Jambaló', 'La Sierra', 'La Vega', 'López', 'Mercaderes', 'Miranda', 'Morales', 'Padilla',
  ],
  'Cesar': [
    'Valledupar', 'Aguachica', 'Agustín Codazzi', 'Astrea', 'Becerril', 'Bosconia',
    'Chimichagua', 'Chiriguaná', 'Curumaní', 'El Copey', 'El Paso', 'Gamarra', 'González',
    'La Gloria', 'La Jagua de Ibirico', 'La Paz', 'Manaure Balcón del Cesar', 'Pailitas',
    'Pelaya', 'Pueblo Bello', 'Río de Oro', 'Robles', 'San Alberto', 'San Diego', 'San Martín',
  ],
  'Chocó': [
    'Quibdó', 'Acandí', 'Alto Baudó', 'Atrato', 'Bagadó', 'Bahía Solano', 'Bajo Baudó',
    'Bojayá', 'Cértegui', 'Condoto', 'El Cantón del San Pablo', 'El Carmen de Atrato', 'Istmina',
    'Juradó', 'Lloró', 'Medio Atrato', 'Medio Baudó', 'Medio San Juan', 'Nóvita', 'Nuquí',
    'Río Iro', 'Río Quito', 'Riosucio', 'San José del Palmar', 'Sipí', 'Tadó', 'Unguía',
  ],
  'Córdoba': [
    'Montería', 'Ayapel', 'Buenavista', 'Canalete', 'Cereté', 'Chimá', 'Chinú',
    'Ciénaga de Oro', 'Cotorra', 'La Apartada', 'Lorica', 'Los Córdobas', 'Momil',
    'Montelíbano', 'Moñitos', 'Planeta Rica', 'Pueblo Nuevo', 'Puerto Escondido', 'Puerto Libertador',
    'Purísima', 'Sahagún', 'San Andrés de Sotavento', 'San Antero', 'San Bernardo del Viento',
    'San Carlos', 'San José de Uré', 'San Pelayo', 'Tierralta', 'Tuchín', 'Valencia',
  ],
  'Cundinamarca': [
    'Bogotá D.C.', 'Agua de Dios', 'Albán', 'Anapoima', 'Anolaima', 'Arbeláez', 'Beltrán',
    'Bituima', 'Bojacá', 'Cabrera', 'Cachipay', 'Cajicá', 'Caparrapí', 'Cáqueza', 'Carmen de Carupa',
    'Chaguaní', 'Chía', 'Chipaque', 'Choachí', 'Chocontá', 'Cogua', 'Cota', 'Cucunubá',
    'El Colegio', 'Facatativá', 'Fusagasugá', 'Girardot', 'Guatavita', 'La Calera', 'Madrid',
    'Mosquera', 'Sibaté', 'Soacha', 'Sopó', 'Tabio', 'Tenjo', 'Tocancipá', 'Zipaquirá',
  ],
  'Guainía': [
    'Inírida', 'Barranco Minas', 'Cacahual', 'La Guadalupe', 'Mapiripana', 'Morichal',
    'Pana Pana', 'Puerto Colombia', 'San Felipe',
  ],
  'Guaviare': [
    'San José del Guaviare', 'Calamar', 'El Retorno', 'Miraflores',
    'Barranquillita', 'La Libertad', 'Morichal Nuevo', 'Puerto Arturo', 'Puerto Concordia',
  ],
  'Huila': [
    'Neiva', 'Acevedo', 'Agrado', 'Aipe', 'Algeciras', 'Altamira', 'Baraya', 'Campoalegre',
    'Colombia', 'Elías', 'Garzón', 'Gigante', 'Guadalupe', 'Hobo', 'Íquira', 'Isnos',
    'La Argentina', 'La Plata', 'Nátaga', 'Oporapa', 'Paicol', 'Palermo', 'Palestina',
    'Pital', 'Pitalito', 'Rivera', 'Saladoblanco', 'San Agustín', 'Santa María', 'Suaza',
    'Tarqui', 'Tello', 'Teruel', 'Tesalia', 'Timaná', 'Villavieja', 'Yaguará',
  ],
  'La Guajira': [
    'Riohacha', 'Albania', 'Barrancas', 'Dibulla', 'Distracción', 'El Molino', 'Fonseca',
    'Hatonuevo', 'La Jagua del Pilar', 'Maicao', 'Manaure', 'San Juan del Cesar', 'Uribia',
    'Urumita', 'Villanueva',
  ],
  'Magdalena': [
    'Santa Marta', 'Algarrobo', 'Aracataca', 'Ariguaní', 'Cerro de San Antonio', 'Chivolo',
    'Ciénaga', 'Concordia', 'El Banco', 'El Piñón', 'El Retén', 'Fundación', 'Guamal',
    'Nueva Granada', 'Pedraza', 'Pijiño del Carmen', 'Pivijay', 'Plato', 'Puebloviejo',
    'Remolino', 'Sabanas de San Ángel', 'Salamina', 'San Sebastián de Buenavista', 'San Zenón',
    'Santa Ana', 'Santa Bárbara de Pinto', 'Sitionuevo', 'Tenerife', 'Zapayán', 'Zona Bananera',
  ],
  'Meta': [
    'Villavicencio', 'Acacías', 'Barranca de Upía', 'Cabuyaro', 'Castilla la Nueva', 'Cubarral',
    'Cumaral', 'El Calvario', 'El Castillo', 'El Dorado', 'Fuente de Oro', 'Granada',
    'Guamal', 'La Macarena', 'La Uribe', 'Lejanías', 'Mapiripán', 'Mesetas', 'Puerto Concordia',
    'Puerto Gaitán', 'Puerto Lleras', 'Puerto López', 'Puerto Rico', 'Restrepo', 'San Carlos de Guaroa',
    'San Juan de Arama', 'San Juanito', 'San Martín', 'Vistahermosa',
  ],
  'Nariño': [
    'Pasto', 'Albán', 'Aldana', 'Ancuyá', 'Arboleda', 'Barbacoas', 'Belén', 'Buesaco',
    'Colón', 'Consacá', 'Contadero', 'Córdoba', 'Cuaspud', 'Cumbal', 'Cumbitara', 'El Charco',
    'El Peñol', 'El Rosario', 'El Tablón de Gómez', 'El Tambo', 'Funes', 'Guachucal',
    'Guaitarilla', 'Gualmatán', 'Iles', 'Imués', 'Ipiales', 'La Cruz', 'La Florida', 'La Llanada',
    'La Tola', 'La Unión', 'Leiva', 'Linares', 'Los Andes', 'Magüí', 'Mallama', 'Mosquera',
    'Nariño', 'Olaya Herrera', 'Ospina', 'Roberto Payán', 'Samaniego', 'Sandoná', 'San Bernardo',
    'San Lorenzo', 'San Pablo', 'Santa Bárbara', 'Sapuyes', 'Taminango', 'Tangua', 'Túquerres',
  ],
  'Norte de Santander': [
    'Cúcuta', 'Ábrego', 'Arboledas', 'Bochalema', 'Bucarasica', 'Cácota', 'Cáchira', 'Chinácota',
    'Chitagá', 'Convención', 'Cucutilla', 'Durania', 'El Carmen', 'El Tarra', 'El Zulia',
    'Gramalote', 'Hacarí', 'Herrán', 'La Esperanza', 'La Playa', 'Labateca', 'Los Patios',
    'Lourdes', 'Mutiscua', 'Ocaña', 'Pamplona', 'Pamplonita', 'Puerto Santander', 'Ragonvalia',
    'Salazar', 'San Calixto', 'San Cayetano', 'Santiago', 'Sardinata', 'Silos', 'Teorama',
    'Tibú', 'Toledo', 'Villacaro', 'Villa del Rosario',
  ],
  'Putumayo': [
    'Mocoa', 'Colón', 'Orito', 'Puerto Asís', 'Puerto Caicedo', 'Puerto Guzmán', 'Puerto Leguízamo',
    'San Francisco', 'San Miguel', 'Santiago', 'Sibundoy', 'Valle del Guamuez', 'Villagarzón',
  ],
  'Quindío': [
    'Armenia', 'Buenavista', 'Calarcá', 'Circasia', 'Córdoba', 'Filandia', 'Génova',
    'La Tebaida', 'Montenegro', 'Pijao', 'Quimbaya', 'Salento',
  ],
  'Risaralda': [
    'Pereira', 'Apía', 'Balboa', 'Belén de Umbría', 'Dosquebradas', 'Guática', 'La Celia',
    'La Virginia', 'Marsella', 'Mistrató', 'Pueblo Rico', 'Quinchía', 'Santa Rosa de Cabal',
    'Santuario',
  ],
  'San Andrés y Providencia': [
    'San Andrés', 'Providencia', 'Santa Catalina',
    'La Loma', 'San Luis', 'El Cove', 'North End', 'Sound Bay', 'Old Providence', 'Bottom House',
  ],
  'Santander': [
    'Bucaramanga', 'Aguada', 'Albania', 'Aratoca', 'Barbosa', 'Barichara', 'Barrancabermeja',
    'Betulia', 'Bolívar', 'Cabrera', 'California', 'Capitanejo', 'Carcasí', 'Cepitá', 'Cerrito',
    'Charalá', 'Charta', 'Chimá', 'Chipatá', 'Cimitarra', 'Concepción', 'Confines', 'Contratación',
    'Coromoro', 'Curití', 'El Carmen de Chucurí', 'El Guacamayo', 'El Playón', 'Encino', 'Floridablanca',
    'Galán', 'Gámbita', 'Girón', 'Guaca', 'Guavatá', 'Güepsa', 'Hato', 'Jesús María',
    'Landázuri', 'La Belleza', 'Lebrija', 'Los Santos', 'Macaravita', 'Málaga', 'Matanza',
    'Mogotes', 'Molagavita', 'Ocamonte', 'Oiba', 'Onzaga', 'Palmar', 'Palmas del Socorro',
    'Páramo', 'Piedecuesta', 'Pinchote', 'Puente Nacional', 'Puerto Parra', 'Puerto Wilches',
    'Rionegro', 'Sabana de Torres', 'San Andrés', 'San Benito', 'San Gil', 'Vélez',
  ],
  'Sucre': [
    'Sincelejo', 'Buenavista', 'Caimito', 'Coloso', 'Corozal', 'Coveñas', 'Chalán',
    'El Roble', 'Galeras', 'Guaranda', 'La Unión', 'Los Palmitos', 'Majagual', 'Morroa',
    'Ovejas', 'Palmito', 'Sampués', 'San Benito Abad', 'San Juan de Betulia', 'San Marcos',
    'San Onofre', 'San Pedro', 'Santiago de Tolú', 'Toluviejo',
  ],
  'Tolima': [
    'Ibagué', 'Alpujarra', 'Alvarado', 'Ambalema', 'Anzoátegui', 'Armero', 'Ataco',
    'Cajamarca', 'Carmen de Apicalá', 'Casabianca', 'Chaparral', 'Coello', 'Coyaima',
    'Cunday', 'Dolores', 'Espinal', 'Falan', 'Flandes', 'Fresno', 'Guamo', 'Herveo',
    'Honda', 'Icononzo', 'Lérida', 'Líbano', 'Mariquita', 'Melgar', 'Murillo', 'Natagaima',
    'Ortega', 'Palocabildo', 'Piedras', 'Planadas', 'Prado', 'Purificación', 'Rioblanco',
    'Roncesvalles', 'Rovira', 'Saldaña', 'San Antonio', 'San Luis', 'Santa Isabel', 'Suárez',
    'Valle de San Juan', 'Venadillo', 'Villahermosa', 'Villarrica',
  ],
  'Valle del Cauca': [
    'Cali', 'Alcalá', 'Andalucía', 'Ansermanuevo', 'Argelia', 'Bolívar', 'Buenaventura',
    'Bugalagrande', 'Caicedonia', 'Calima', 'Candelaria', 'Cartago', 'Dagua', 'El Águila',
    'El Cairo', 'El Cerrito', 'El Dovio', 'Florida', 'Ginebra', 'Guacarí', 'Jamundí',
    'La Cumbre', 'La Unión', 'La Victoria', 'Obando', 'Palmira', 'Pradera', 'Restrepo',
    'Riofrío', 'Roldanillo', 'San Pedro', 'Sevilla', 'Toro', 'Trujillo', 'Tuluá',
    'Ulloa', 'Versalles', 'Vijes', 'Yotoco', 'Yumbo', 'Zarzal',
  ],
  'Vaupés': [
    'Mitú', 'Carurú', 'Pacoa', 'Papunaua', 'Taraira', 'Yavaraté',
    'La Guadalupe', 'Monfort', 'Puerto Vaupés', 'Acaricuara',
  ],
  'Vichada': [
    'Puerto Carreño', 'Cumaribo', 'La Primavera', 'Santa Rosalía',
    'Casuarito', 'La Victoria', 'Barrancominas', 'San José de Ocune', 'Amanaven', 'Puerto Príncipe',
  ],
}


// ── Lista ordenada de departamentos (Derivado de MUNICIPIOS_POR_DEPARTAMENTO) ──
export const DEPARTAMENTOS: string[] = Object.keys(MUNICIPIOS_POR_DEPARTAMENTO).sort(
  (a, b) => a.localeCompare(b, 'es')
)

// ── Capitales por Departamento (Derivado de MUNICIPIOS_POR_DEPARTAMENTO) ─────────
export const CAPITALES: Record<string, string> = Object.keys(MUNICIPIOS_POR_DEPARTAMENTO).reduce((acc, depto) => {
  acc[depto] = MUNICIPIOS_POR_DEPARTAMENTO[depto][0]
  return acc
}, {} as Record<string, string>)

// ── Helper: obtener municipios de un departamento ───────────────
export function getMunicipios(departamento: string): string[] {
  return MUNICIPIOS_POR_DEPARTAMENTO[departamento] ?? []
}

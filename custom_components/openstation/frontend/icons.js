// Crossed-out icons that Material Design Icons does not have.
//
// Derived from mdi:escalator and mdi:walk (https://pictogrammers.com/library/mdi/),
// Apache License 2.0, https://www.apache.org/licenses/LICENSE-2.0. Changed: a slash was
// added in the style of the MDI "-off" icons, and the head of the escalator figure moved
// clear of it.
const ICONS = {
  "escalator-off":
    "M18.95 8 13.8 13.15 22.11 21.46 20.84 22.73 7.35 9.24 1.11 3 2.39 1.73 10.97 10.32 17.29 4H20C21.1 4 22 4.9 22 6C22 7.1 21.1 8 20 8ZM7 11.99 10.98 15.97 6.95 20H4C2.9 20 2 19.1 2 18C2 16.9 2.9 16 4 16H5.29L7 14.29ZM10.7 5.8C10.7 6.63 10.03 7.3 9.2 7.3C8.37 7.3 7.7 6.63 7.7 5.8C7.7 4.97 8.37 4.3 9.2 4.3C10.03 4.3 10.7 4.97 10.7 5.8Z",
  "travelator-off":
    "M9.38 8.73 13.05 12.39 22.11 21.46 20.84 22.73 14.8 16.69V22H13V17L10.67 13.89L7.8 22H6L8.87 10.76L7.8 9.69V11H6V7.89L1.11 3L2.39 1.73L6.35 5.69L7.94 7.29ZM19 10H14.12L13.04 8.18L12.82 9.06L8.71 4.95L11.42 4.11C11.58 4.06 11.74 4.03 11.92 4.03C12.54 4.03 13.08 4.37 13.38 4.87L15.38 8.2H19ZM15.8 2C15.8 3 15 3.8 14 3.8C13 3.8 12.2 3 12.2 2C12.2 1 13 0.2 14 0.2C15 0.2 15.8 1 15.8 2Z",
};

window.customIcons ??= {};
window.customIcons.openstation = {
  getIcon: async (name) => ({ path: ICONS[name] }),
  getIconList: async () => Object.keys(ICONS).map((name) => ({ name })),
};

// plugins/docs-global-data/index.js
export default function docsGlobalDataPlugin(context, options) {
    return {
        name: 'docusaurus-plugin-docs-global-data',

        async allContentLoaded({ allContent, actions }) {
            const { setGlobalData } = actions;
            const docsPluginData = allContent['docusaurus-plugin-content-docs'];

            if (!docsPluginData?.default?.loadedVersions) {
                setGlobalData([]);
                return;
            }

            const docsInstanceData = docsPluginData.default;
            const currentVersion = docsInstanceData.loadedVersions.find(
                (version) => version.versionName === 'current'
            );

            if (!currentVersion) {
                setGlobalData([]);
                return;
            }

            const allDocs = currentVersion.docs;

            // Filtramos para asegurarnos de que el doc tenga todo lo necesario para la tarjeta
            const processedDocs = allDocs
                .filter((doc) =>
                    doc.frontMatter &&
                    doc.frontMatter.date &&
                    doc.frontMatter.description && // <-- Nuevo filtro
                    doc.frontMatter.image          // <-- Nuevo filtro
                )
                .map((doc) => ({
                    title: doc.title,
                    permalink: doc.permalink,
                    date: doc.frontMatter.date,
                    description: doc.frontMatter.description, // <-- Nuevo dato
                    image: doc.frontMatter.image,          // <-- Nuevo dato
                }));

            const sortedDocs = processedDocs.sort((a, b) => new Date(b.date) - new Date(a.date));

            setGlobalData(sortedDocs.slice(0, 3)); // Mostramos solo las 3 tarjetas más recientes
        },
    };
}